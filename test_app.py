import pytest
from ratemybronco import app


@pytest.fixture
def client():
  return app.test_client()


def test_landing(client):
  assert client.get("/").status_code == 200

def test_landing_post(client):
  assert client.post('/').status_code == 405