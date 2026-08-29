"""Highlight routes: detect trigger, list, update (timeline adjust), delete, ownership."""


def test_detect_highlights_requires_transcript(client, auth_headers, project):
    response = client.post(f"/api/projects/{project.id}/highlights/detect", json={}, headers=auth_headers)
    assert response.status_code == 400


def test_detect_highlights_queues_background_task(client, auth_headers, project, transcript):
    response = client.post(f"/api/projects/{project.id}/highlights/detect", json={"num_shorts": 4}, headers=auth_headers)
    assert response.status_code == 202


def test_detect_highlights_forbidden_for_other_user(client, other_auth_headers, project, transcript):
    response = client.post(f"/api/projects/{project.id}/highlights/detect", json={}, headers=other_auth_headers)
    assert response.status_code == 403


def test_list_highlights(client, auth_headers, project, highlight):
    response = client.get(f"/api/projects/{project.id}/highlights", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == highlight.id


def test_update_highlight_persists_timeline_adjustment(client, auth_headers, project, highlight):
    response = client.put(
        f"/api/projects/{project.id}/highlights/{highlight.id}",
        json={"start_time": 5.0, "end_time": 20.0},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["start_time"] == 5.0
    assert body["end_time"] == 20.0


def test_update_highlight_rejects_over_60_seconds(client, auth_headers, project, highlight):
    response = client.put(
        f"/api/projects/{project.id}/highlights/{highlight.id}",
        json={"start_time": 0.0, "end_time": 90.0},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_update_highlight_rejects_invalid_range(client, auth_headers, project, highlight):
    response = client.put(
        f"/api/projects/{project.id}/highlights/{highlight.id}",
        json={"start_time": 10.0, "end_time": 5.0},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_update_highlight_forbidden_for_other_user(client, other_auth_headers, project, highlight):
    response = client.put(
        f"/api/projects/{project.id}/highlights/{highlight.id}",
        json={"title": "hacked"},
        headers=other_auth_headers,
    )
    assert response.status_code == 403


def test_delete_highlight(client, auth_headers, project, highlight):
    response = client.delete(f"/api/projects/{project.id}/highlights/{highlight.id}", headers=auth_headers)
    assert response.status_code == 204
    listing = client.get(f"/api/projects/{project.id}/highlights", headers=auth_headers)
    assert listing.json() == []


def test_delete_highlight_not_found(client, auth_headers, project):
    response = client.delete(f"/api/projects/{project.id}/highlights/999999", headers=auth_headers)
    assert response.status_code == 404
