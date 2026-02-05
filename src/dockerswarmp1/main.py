import asyncio
import hashlib
import hmac
import os
import socket
import time
from pathlib import Path
from typing import Annotated

import uvloop
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

app = FastAPI()

WEBHOOK_DIR = Path("/app/webhook_jobs")


def load_secret(name: str) -> str:
  value = os.getenv(name)
  if value:
    return value

  file_path = os.getenv(f"{name}_FILE")
  if file_path:
    secret_path = Path(file_path)
    if secret_path.is_file():
      return secret_path.read_text(encoding="utf-8").strip()

  raise RuntimeError(f"Missing required secret: {name}")


WEBHOOK_SECRET = load_secret("GITHUB_WEBHOOK_SECRET")


@app.get("/")
async def root() -> str:
  loop = asyncio.get_event_loop()

  if isinstance(loop, uvloop.loop.Loop):
    return f"FIM DO VÍDEO - {socket.gethostname()}"

  return socket.gethostname()


@app.get("/health")
async def health_check() -> dict[str, str]:
  return {"status": "healthy"}


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
