def test_list_leagues_has_epl(client):
    r = client.get("/leagues")
    assert r.status_code == 200
    leagues = r.json()
    assert any(x["code"] == "EPL" for x in leagues)


def test_get_league_not_found(client):
    r = client.get("/leagues/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "League not found"


def test_list_league_seasons(client):
    leagues = client.get("/leagues").json()
    epl = next(x for x in leagues if x["code"] == "EPL")
    r = client.get(f"/leagues/{epl['id']}/seasons")
    assert r.status_code == 200
    seasons = r.json()
    assert len(seasons) >= 1
    assert seasons[0]["name"] == "2024-25"
