def test_health_db(client):
    r = client.get("/health/db")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "football_ai"
    assert body["public_table_count"] >= 23
