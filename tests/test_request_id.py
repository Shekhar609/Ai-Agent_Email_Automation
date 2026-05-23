async def test_response_has_request_id_header(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    lower = {k.lower() for k in resp.headers.keys()}
    assert "x-request-id" in lower


async def test_request_id_echoed_when_supplied(client):
    custom = "test-rid-deadbeef-1234"
    resp = await client.get("/api/health", headers={"X-Request-ID": custom})
    assert resp.headers.get("x-request-id") == custom


async def test_request_id_unique_per_call(client):
    r1 = await client.get("/api/health")
    r2 = await client.get("/api/health")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]
