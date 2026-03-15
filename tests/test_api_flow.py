def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_auth_duplicate_user(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "Passw0rd!"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409


def test_project_and_task_flow(client, token):
    headers = {"Authorization": f"Bearer {token}"}

    project = client.post("/projects", json={"name": "platform", "description": "cicd"}, headers=headers)
    assert project.status_code == 201
    project_id = project.json()["id"]

    t1 = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "write pipeline", "detail": "tekton", "priority": 2},
        headers=headers,
    )
    assert t1.status_code == 201

    t2 = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "write tests", "detail": "pytest", "priority": 1},
        headers=headers,
    )
    assert t2.status_code == 201
    task_id = t2.json()["id"]

    patch = client.patch(
        f"/projects/{project_id}/tasks/{task_id}",
        json={"status": "in_progress", "priority": 3},
        headers=headers,
    )
    assert patch.status_code == 200
    assert patch.json()["status"] == "in_progress"

    filtered = client.get(f"/projects/{project_id}/tasks?status=in_progress", headers=headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1


def test_unauthorized_access_rejected(client):
    r = client.get("/projects")
    assert r.status_code == 401
