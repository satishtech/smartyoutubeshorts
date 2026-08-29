"""Auth: register/login/refresh/logout, google CSRF check, /me."""


def test_register(client):
    response = client.post(
        "/api/auth/register", json={"email": "new@test.com", "password": "password123", "full_name": "New"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@test.com"
    assert "hashed_password" not in body


def test_register_duplicate_email_conflicts(client, test_user):
    response = client.post("/api/auth/register", json={"email": test_user.email, "password": "password123"})
    assert response.status_code == 409


def test_register_short_password_rejected(client):
    response = client.post("/api/auth/register", json={"email": "short@test.com", "password": "abc"})
    assert response.status_code == 422


def test_login_success(client, test_user):
    response = client.post("/api/auth/login", json={"email": test_user.email, "password": "password123"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    response = client.post("/api/auth/login", json={"email": test_user.email, "password": "wrong"})
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post("/api/auth/login", json={"email": "nope@test.com", "password": "password123"})
    assert response.status_code == 401


def test_me_unauthorized(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_authorized(client, auth_headers, test_user):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


def test_update_me(client, auth_headers):
    response = client.put("/api/auth/me", json={"full_name": "Updated Name"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_refresh_flow_rotates_token(client, test_user):
    login = client.post("/api/auth/login", json={"email": test_user.email, "password": "password123"})
    refresh_token = login.json()["refresh_token"]

    response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != refresh_token

    # Old refresh token should now be revoked and unusable.
    reuse = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse.status_code == 401


def test_refresh_invalid_token_rejected(client):
    response = client.post("/api/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client, test_user, db):
    login = client.post("/api/auth/login", json={"email": test_user.email, "password": "password123"})
    refresh_token = login.json()["refresh_token"]

    response = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 204

    reuse = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse.status_code == 401


def test_google_login_redirects_and_sets_state_cookie(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "fake-client-id")
    response = client.get("/api/auth/google", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "accounts.google.com" in response.headers["location"]
    assert "oauth_state" in response.cookies


def test_google_login_not_configured(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    response = client.get("/api/auth/google", follow_redirects=False)
    assert response.status_code == 400


def test_google_callback_rejects_bad_state(client):
    response = client.get(
        "/api/auth/google/callback",
        params={"code": "abc", "state": "mismatched-state"},
        cookies={"oauth_state": "expected-state"},
    )
    assert response.status_code == 401
