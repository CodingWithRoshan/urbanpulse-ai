import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-please-change")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)
