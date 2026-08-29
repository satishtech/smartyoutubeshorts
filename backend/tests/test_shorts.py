"""Short routes: generate trigger, list, stream, download, zip export, ownership."""

import pytest

from app.models.short import Short, ShortStatus


def test_generate_shorts_requires_highlights(client, auth_headers, project):
    response = client.post(f"/api/projects/{project.id}/shorts/generate", json={}, headers=auth_headers)
    assert response.status_code == 400


def test_generate_shorts_queues_background_task(client, auth_headers, project, highlight):
    response = client.post(f"/api/projects/{project.id}/shorts/generate", json={}, headers=auth_headers)
    assert response.status_code == 202


def test_generate_shorts_rejects_foreign_highlight_ids(client, auth_headers, project, highlight):
    response = client.post(
        f"/api/projects/{project.id}/shorts/generate",
        json={"highlight_segment_ids": [999999]},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_generate_shorts_forbidden_for_other_user(client, other_auth_headers, project, highlight):
    response = client.post(f"/api/projects/{project.id}/shorts/generate", json={}, headers=other_auth_headers)
    assert response.status_code == 403


def test_list_shorts_empty(client, auth_headers, project):
    response = client.get(f"/api/projects/{project.id}/shorts", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.fixture
def ready_short(db, project, highlight, tmp_path) -> Short:
    video_path = tmp_path / "short.mp4"
    video_path.write_bytes(b"fake mp4 bytes " * 100)
    short = Short(
        project_id=project.id,
        highlight_segment_id=highlight.id,
        file_path=str(video_path),
        thumbnail_path=None,
        duration_seconds=10.0,
        has_subtitles=True,
        has_broll=False,
        status=ShortStatus.ready,
    )
    db.add(short)
    db.commit()
    db.refresh(short)
    return short


def test_list_shorts(client, auth_headers, project, ready_short):
    response = client.get(f"/api/projects/{project.id}/shorts", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "ready"


def test_download_short(client, auth_headers, ready_short):
    response = client.get(f"/api/shorts/{ready_short.id}/download", headers=auth_headers)
    assert response.status_code == 200
    assert response.content.startswith(b"fake mp4 bytes")


def test_download_short_forbidden_for_other_user(client, other_auth_headers, ready_short):
    response = client.get(f"/api/shorts/{ready_short.id}/download", headers=other_auth_headers)
    assert response.status_code == 403


def test_download_short_not_found(client, auth_headers):
    response = client.get("/api/shorts/999999/download", headers=auth_headers)
    assert response.status_code == 404


def test_stream_short_full(client, auth_headers, ready_short):
    response = client.get(f"/api/shorts/{ready_short.id}/stream", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["accept-ranges"] == "bytes"


def test_stream_short_with_range(client, auth_headers, ready_short):
    response = client.get(
        f"/api/shorts/{ready_short.id}/stream", headers={**auth_headers, "Range": "bytes=0-9"}
    )
    assert response.status_code == 206
    assert len(response.content) == 10


def test_download_zip(client, auth_headers, project, ready_short):
    response = client.get(f"/api/projects/{project.id}/download-zip", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


def test_download_zip_no_shorts(client, auth_headers, project):
    response = client.get(f"/api/projects/{project.id}/download-zip", headers=auth_headers)
    assert response.status_code == 404


def test_download_zip_forbidden_for_other_user(client, other_auth_headers, project, ready_short):
    response = client.get(f"/api/projects/{project.id}/download-zip", headers=other_auth_headers)
    assert response.status_code == 403


def test_list_shorts_includes_highlight_info_and_has_thumbnail(client, auth_headers, project, ready_short, highlight):
    response = client.get(f"/api/projects/{project.id}/shorts", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["has_thumbnail"] is False
    assert body[0]["highlight_title"] == highlight.title
    assert body[0]["highlight_start_time"] == highlight.start_time
    assert body[0]["highlight_end_time"] == highlight.end_time
    assert "file_path" not in body[0]
    assert "thumbnail_path" not in body[0]


def test_get_short_thumbnail_not_found(client, auth_headers, ready_short):
    response = client.get(f"/api/shorts/{ready_short.id}/thumbnail", headers=auth_headers)
    assert response.status_code == 404


def test_get_short_thumbnail_forbidden_for_other_user(client, other_auth_headers, ready_short):
    response = client.get(f"/api/shorts/{ready_short.id}/thumbnail", headers=other_auth_headers)
    assert response.status_code == 403


def test_get_short_thumbnail_missing_returns_404(client, auth_headers):
    response = client.get("/api/shorts/999999/thumbnail", headers=auth_headers)
    assert response.status_code == 404


def test_get_short_thumbnail_streams_when_present(client, auth_headers, db, ready_short, tmp_path):
    thumb_path = tmp_path / "short_thumb.jpg"
    thumb_path.write_bytes(b"fake short jpeg")
    ready_short.thumbnail_path = str(thumb_path)
    db.add(ready_short)
    db.commit()

    response = client.get(f"/api/shorts/{ready_short.id}/thumbnail", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b"fake short jpeg"

    list_response = client.get(f"/api/projects/{ready_short.project_id}/shorts", headers=auth_headers)
    assert list_response.json()[0]["has_thumbnail"] is True
