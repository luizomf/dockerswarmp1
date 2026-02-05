import os

import pytest
from fastapi.testclient import TestClient

os.environ["GITHUB_WEBHOOK_SECRET"] = "TEST_SECRET_VALUE"  # noqa: S105

from dockerswarmp1.main import app


@pytest.fixture
def client():
  """Make a new client for you to use on tests"""
  return TestClient(app)
