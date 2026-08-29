"""Project routes: create (upload/youtube), list, get, delete, status, ownership."""
import io


def test_create_project_with_youtube_url(client, auth_headers):
    response = client.post(
        "/api/projects",
        json={"title": "My Video", "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "num_shorts_requested": 5},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "youtube_url"
    assert body["num_shorts_requested"] == 5
    assert body["status"] == "pending"


def test_create_project_invalid_youtube_url(client, auth_headers):
    response = client.post(
        "/api/projects",
        json={"youtube_url": "https://example.com/not-youtube"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_create_project_num_shorts_out_of_range(client, auth_headers):
    response = client.post(
        "/api/projects",
        json={"youtube_url": "https://youtu.be/dQw4w9WgXcQ", "num_shorts_requested": 11},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_create_project_requires_source(client, auth_headers):
    response = client.post("/api/projects", json={"title": "No source"}, headers=auth_headers)
    assert response.status_code == 400


def test_create_project_unauthenticated(client):
    response = client.post("/api/projects", json={"youtube_url": "https://youtu.be/dQw4w9WgXcQ"})
    assert response.status_code == 401


def test_create_project_with_file_upload(client, auth_headers):
    fake_video = io.BytesIO(b"\x00\x00\x00\x18ftypmp42fake video bytes for testing")
    response = client.post(
        "/api/projects",
        data={"title": "Uploaded", "num_shorts_requested": "2"},
        files={"file": ("clip.mp4", fake_video, "video/mp4")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "upload"
    assert body["title"] == "Uploaded"


def test_create_project_rejects_bad_file_extension(client, auth_headers):
    fake_file = io.BytesIO(b"not a video")
    response = client.post(
        "/api/projects",
        data={"title": "Bad file"},
        files={"file": ("notes.txt", fake_file, "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_list_projects_only_returns_own(client, auth_headers, other_auth_headers):
    client.post("/api/projects", json={"youtube_url": "https://youtu.be/dQw4w9WgXcQ"}, headers=auth_headers)
    client.post("/api/projects", json={"youtube_url": "https://youtu.be/dQw4w9WgXcQ"}, headers=other_auth_headers)

    response = client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_get_project(client, auth_headers, project):
    response = client.get(f"/api/projects/{project.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == project.id


def test_get_project_not_found(client, auth_headers):
    response = client.get("/api/projects/999999", headers=auth_headers)
    assert response.status_code == 404


def test_get_project_forbidden_for_other_user(client, other_auth_headers, project):
    response = client.get(f"/api/projects/{project.id}", headers=other_auth_headers)
    assert response.status_code == 403


def test_delete_project(client, auth_headers, project):
    response = client.delete(f"/api/projects/{project.id}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"/api/projects/{project.id}", headers=auth_headers).status_code == 404


def test_delete_project_forbidden_for_other_user(client, other_auth_headers, project):
    response = client.delete(f"/api/projects/{project.id}", headers=other_auth_headers)
    assert response.status_code == 403


def test_get_project_status(client, auth_headers, project):
    response = client.get(f"/api/projects/{project.id}/status", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == project.status.value
