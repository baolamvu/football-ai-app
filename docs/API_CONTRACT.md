# API Contract (Phase 1)

Base URL (local): `http://127.0.0.1:8000`

Interactive docs: `/docs`

## Error format

All application errors return:

```json
{"detail": "Human-readable message"}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request (invalid query) |
| 404 | Not found |
| 500 | Server error |

---

## Endpoints

### `GET /`
Health message (no DB).

### `GET /health/db`
Database connectivity check.

**Response `200`:**
```json
{
  "status": "ok",
  "database": "football_ai",
  "public_table_count": 24
}
```

---

### `GET /leagues`
List all leagues.

**Response `200`:** array of `LeagueOut`

| Field | Type |
|-------|------|
| id | int |
| code | string |
| name | string |
| country | string \| null |
| tier | int \| null |
| created_at | datetime |

---

### `GET /leagues/{league_id}`
Single league. **404** if missing.

---

### `GET /leagues/{league_id}/seasons`
Seasons for a league. **404** if league missing.

**Response `200`:** array of `SeasonOut`

| Field | Type |
|-------|------|
| id | int |
| league_id | int |
| name | string |
| start_date | date |
| end_date | date |
| matchweeks | int \| null |
| created_at | datetime |

---

### `GET /seasons/{season_id}`
Single season. **404** if missing.

---

### `GET /seasons/{season_id}/matches`
Matches in a season.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| status | string | `scheduled`, `live`, `finished`, `postponed`, `cancelled` |
| from_date | date | Kickoff >= date (UTC) |
| to_date | date | Kickoff <= date (UTC) |

**Response `200`:** array of `MatchOut`

---

### `GET /matches`
List matches (all leagues).

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| league_id | int | Filter by league |
| season_id | int | Filter by season |
| status | string | See statuses above |
| from_date | date | Kickoff >= date |
| to_date | date | Kickoff <= date |

**400** if `status` invalid or `from_date` > `to_date`.

---

### `GET /matches/{match_id}`
Match detail (includes `competition_phase`, `neutral_site`).

**404** if missing.

---

### `GET /matches/{match_id}/prediction`
Win / draw / lose probabilities (%).

**Response `200`:** `PredictionOut`

| Field | Type |
|-------|------|
| match_id | int |
| home_team | string |
| away_team | string |
| home_win | float |
| draw | float |
| away_win | float |
| model_name | string |
| source | `"stored"` \| `"computed"` |
| notes | string \| null |

---

### `GET /prediction?home=&away=` (legacy)
Find latest match by team names; same `PredictionOut` shape. **404** if teams or match not found.

---

## Typical Flutter flow

1. `GET /leagues` → user picks league  
2. `GET /leagues/{id}/seasons` → pick season (optional)  
3. `GET /seasons/{id}/matches?status=scheduled` → fixture list  
4. `GET /matches/{id}` + `GET /matches/{id}/prediction` → match screen  

---

## Prerequisites

- PostgreSQL running, schema applied (`scripts/init_database.py`)
- Sample data (`python scripts/seed_sample.py`)
- `.env` with valid `POSTGRES_*`
