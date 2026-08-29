"""Transcript route: fetch + ownership."""


def test_get_transcript(client, auth_headers, project, transcript):
    response = client.get(f"/api/projects/{project.id}/transcript", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["full_text"] == transcript.full_text
    assert len(body["segments"]) == 2


def test_get_transcript_not_found(client, auth_headers, project):
    response = client.get(f"/api/projects/{project.id}/transcript", headers=auth_headers)
    assert response.status_code == 404


def test_get_transcript_forbidden_for_other_user(client, other_auth_headers, project, transcript):
    response = client.get(f"/api/projects/{project.id}/transcript", headers=other_auth_headers)
    assert response.status_code == 403


def test_get_transcript_project_not_found(client, auth_headers):
    response = client.get("/api/projects/999999/transcript", headers=auth_headers)
    assert response.status_code == 404
