from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
  """Main route should return status code 200"""
  response = client.get("/")
  assert response.status_code == 200  # noqa: PLR2004


def test_health_check(client: TestClient):
  """Make sure docker health check will work"""
  response = client.get("/health")
  assert response.status_code == 200  # noqa: PLR2004
  assert response.json() == {"status": "healthy"}


def test_visit_counter_requires_db(client: TestClient):
  response = client.get("/api/visit")
  assert response.status_code == 503  # noqa: PLR2004
  assert response.json() == {"detail": "Database not configured"}
