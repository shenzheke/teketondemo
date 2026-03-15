from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    resp = client.get('/healthz')
    assert resp.status_code == 200
    assert resp.json()['status'] == 'ok'


def test_todo_crud() -> None:
    create = client.post('/todos', json={'title': 'learn tekton', 'done': False})
    assert create.status_code == 201
    todo = create.json()
    assert todo['id'] > 0

    read = client.get(f"/todos/{todo['id']}")
    assert read.status_code == 200
    assert read.json()['title'] == 'learn tekton'

    update = client.put(f"/todos/{todo['id']}", json={'title': 'learn tekton deeply', 'done': True})
    assert update.status_code == 200
    assert update.json()['done'] is True

    listed = client.get('/todos')
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    delete = client.delete(f"/todos/{todo['id']}")
    assert delete.status_code == 204
