import asyncio
import hashlib
import hmac
import os
import socket
import time
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import uvloop
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from psycopg import OperationalError
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool

if TYPE_CHECKING:
  from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
  try:
    yield
  finally:
    pool: ConnectionPool[Any] | None = getattr(app.state, "pool", None)
    if pool is not None:
      await asyncio.to_thread(pool.close)
      app.state.pool = None


current_env = os.getenv("CURRENT_ENV", "development").lower()
is_production = current_env == "production"

app = FastAPI(
  lifespan=lifespan,
  # Reduce public attack surface in production. In this project, the API is
  # public on the Internet, and the docs are not required for the demo.
  docs_url=None if is_production else "/docs",
  redoc_url=None if is_production else "/redoc",
  openapi_url=None if is_production else "/openapi.json",
)

WEBHOOK_DIR = Path("/app/webhook_jobs")


class MissingSecretError(RuntimeError):
  def __init__(self, name: str) -> None:
    message = f"Missing required secret: {name}"
    super().__init__(message)


def load_secret(name: str) -> str:
  value = os.getenv(name)
  if value:
    return value

  file_path = os.getenv(f"{name}_FILE")
  if file_path:
    secret_path = Path(file_path)
    if secret_path.is_file():
      return secret_path.read_text(encoding="utf-8").strip()

  raise MissingSecretError(name)


WEBHOOK_SECRET = load_secret("GITHUB_WEBHOOK_SECRET")


def get_database_dsn() -> str | None:
  url = os.getenv("DATABASE_URL")
  if url:
    return url

  database = os.getenv("POSTGRES_DB")
  user = os.getenv("POSTGRES_USER")
  if not database or not user:
    return None

  password = load_secret("POSTGRES_PASSWORD")
  host = os.getenv("POSTGRES_HOST", "postgres")
  port = os.getenv("POSTGRES_PORT", "5432")
  return make_conninfo(
    dbname=database,
    user=user,
    password=password,
    host=host,
    port=port,
  )


def init_db(pool: ConnectionPool[Any]) -> None:
  with pool.connection() as conn:
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS visit_events (
        visit_date date NOT NULL,
        visitor_hash text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (visit_date, visitor_hash)
      )
      """
    )


def get_pool() -> ConnectionPool[Any]:
  existing_pool: ConnectionPool[Any] | None = getattr(app.state, "pool", None)
  if existing_pool is not None:
    return existing_pool

  dsn = get_database_dsn()
  if not dsn:
    raise HTTPException(status_code=503, detail="Database not configured")

  new_pool: ConnectionPool[Any] = ConnectionPool(conninfo=dsn, min_size=1, max_size=5)
  init_db(new_pool)
  app.state.pool = new_pool
  return new_pool


def reset_pool() -> None:
  pool: ConnectionPool[Any] | None = getattr(app.state, "pool", None)
  if pool is None:
    return
  pool.close()
  app.state.pool = None


def get_client_ip(request: Request) -> str:
  forwarded = request.headers.get("x-forwarded-for")
  if forwarded:
    return forwarded.split(",")[0].strip()

  if request.client:
    return request.client.host

  return "unknown"


def build_visit_hash(request: Request, visit_date: date) -> str:
  user_agent = request.headers.get("user-agent", "unknown")
  client_ip = get_client_ip(request)
  visit_salt = os.getenv("VISIT_SALT") or WEBHOOK_SECRET
  raw = f"{visit_date.isoformat()}|{client_ip}|{user_agent}|{visit_salt}"
  return hashlib.sha256(raw.encode()).hexdigest()


def record_visit(pool: ConnectionPool[Any], visit_date: date, visitor_hash: str) -> int:
  with pool.connection() as conn:
    conn.execute(
      """
      INSERT INTO visit_events (visit_date, visitor_hash)
      VALUES (%s, %s)
      ON CONFLICT DO NOTHING
      """,
      (visit_date, visitor_hash),
    )
    cursor = conn.execute(
      "SELECT COUNT(*) FROM visit_events WHERE visit_date = %s",
      (visit_date,),
    )
    result = cursor.fetchone()
    if result is None:
      return 0
    return int(result[0])


@app.get("/")
async def root() -> str:
  loop = asyncio.get_event_loop()

  if isinstance(loop, uvloop.loop.Loop):
    return f"FIM DO VÍDEO - {socket.gethostname()}"

  return socket.gethostname()


@app.get("/health")
async def health_check() -> dict[str, str]:
  return {"status": "healthy"}


@app.get("/api/visit")
async def visit_counter(request: Request) -> dict[str, int | str]:
  visit_date = datetime.now(tz=UTC).date()
  visitor_hash = build_visit_hash(request, visit_date)
  try:
    pool = await asyncio.to_thread(get_pool)
    unique_visits = await asyncio.to_thread(
      record_visit, pool, visit_date, visitor_hash
    )
    return {"date": visit_date.isoformat(), "unique_visits": unique_visits}
  except OperationalError:
    await asyncio.to_thread(reset_pool)
    try:
      pool = await asyncio.to_thread(get_pool)
      unique_visits = await asyncio.to_thread(
        record_visit, pool, visit_date, visitor_hash
      )
      return {"date": visit_date.isoformat(), "unique_visits": unique_visits}
    except OperationalError as exc:
      raise HTTPException(status_code=503, detail="Database unavailable") from exc


def verify_signature(body: bytes, signature_256: str | None) -> None:
  if not signature_256 or not signature_256.startswith("sha256="):
    raise HTTPException(status_code=401, detail="Missing/invalid signature")

  expected = hmac.new(
    WEBHOOK_SECRET.encode(),
    msg=body,
    digestmod=hashlib.sha256,
  ).hexdigest()

  received = signature_256.removeprefix("sha256=")

  if not hmac.compare_digest(expected, received):
    raise HTTPException(status_code=401, detail="Bad signature")


def run_deploy() -> None:
  WEBHOOK_DIR.mkdir(exist_ok=True)
  webhook_deploy_file = WEBHOOK_DIR / str(int(time.time()))
  webhook_deploy_file.touch()


@app.post("/webhook/github")
@app.post("/api/webhook/github")
async def github_webhook(
  request: Request,
  background: BackgroundTasks,
  x_github_event: Annotated[str | None, Header()] = None,
  x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> dict[str, str | bool]:
  body = await request.body()
  verify_signature(body, x_hub_signature_256)

  if x_github_event != "push":
    return {"ok": True, "ignored": "not a push"}

  payload = await request.json()
  if payload.get("ref") != "refs/heads/main":
    return {"ok": True, "ignored": "not main"}

  background.add_task(run_deploy)
  return {"ok": True, "queued": True}
