async def test_google_login_returns_authorize_url(client):
    resp = await client.get("/api/auth/google/login")
    assert resp.status_code == 200
    data = resp.json()
    assert data["authorize_url"].startswith("https://accounts.google.com/")
    assert "state" in data and len(data["state"]) > 16


async def test_google_callback_invalid_state(client):
    resp = await client.get("/api/auth/google/callback", params={"code": "abc", "state": "bogus"})
    assert resp.status_code == 400
    assert "state" in resp.json()["detail"]


async def test_users_me_requires_auth(client):
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


async def test_users_me_rejects_bad_token(client):
    resp = await client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert resp.status_code == 401


async def test_emails_sync_requires_auth(client):
    resp = await client.post("/api/emails/sync")
    assert resp.status_code == 401
