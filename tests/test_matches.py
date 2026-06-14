def test_list_matches(client):
    r = client.get("/matches")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_list_matches_filter_status(client):
    r = client.get("/matches", params={"status": "scheduled"})
    assert r.status_code == 200
    for m in r.json():
        assert m["status"] == "scheduled"


def test_list_matches_bad_status(client):
    r = client.get("/matches", params={"status": "invalid"})
    assert r.status_code == 400


def test_get_match_not_found(client):
    r = client.get("/matches/999999")
    assert r.status_code == 404


def test_season_matches(client):
    epl = next(x for x in client.get("/leagues").json() if x["code"] == "EPL")
    seasons = client.get(f"/leagues/{epl['id']}/seasons").json()
    assert seasons
    sid = seasons[0]["id"]
    r = client.get(f"/seasons/{sid}/matches")
    assert r.status_code == 200
    assert len(r.json()) >= 1
