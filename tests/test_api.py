import os
import pytest

from fastapi.testclient import TestClient

# Ensure main doesn't attempt to load the heavy model during tests
os.environ['SKIP_MODEL_LOAD'] = '1'

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'


def test_classes_endpoint(client):
    r = client.get('/classes')
    assert r.status_code == 200
    data = r.json()
    assert 'classes' in data


def test_medicines_list(client):
    r = client.get('/medicines')
    assert r.status_code == 200
    data = r.json()
    assert 'available_diseases' in data


def test_crud_disease_info_list(client):
    r = client.get('/crud/disease-info')
    assert r.status_code == 200
    data = r.json()
    assert 'available_diseases' in data
