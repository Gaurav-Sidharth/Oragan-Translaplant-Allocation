# Organ Transplant Matching & Allocation Queue

PostgreSQL-backed backend simulation for the OS/DBMS project. This package has a REST API and command-line tools; it intentionally has no frontend. The original Java starter files are retained for reference. The implemented backend is under `backend/`.

## Implemented from the project report

- Relational PostgreSQL tables for donors, organs, recipients, hospitals, hospital distances, allocations, allocation events, and resource locks.
- Composite match/priority index on `(organ_type, blood_type, urgency_score DESC)`, plus deadline and audit lookup indexes.
- Blood-group compatibility filtering and deterministic priority ranking: `urgency * 10 + waiting_days * 2 - distance_km`.
- Organ expiry tracking and a deadline sweep that marks expired, unallocated organs as wasted.
- Safe competing claims using PostgreSQL transactions, `SELECT ... FOR UPDATE`, an explicit resource-lock table, and a unique allocation per organ.
- Append-only allocation event log enforced by a database trigger; a recovery command reconciles allocation state from committed allocation events.
- Controlled wait-for graph deadlock detection/resolution demonstration.
- Allocation success, wastage, and average wait analytics.

This is an academic simulation using synthetic data. Blood type matching and ranking are simplified teaching rules, not clinical allocation guidance.

## Requirements

- Python 3.10+
- Docker Desktop, or a PostgreSQL 14+ database

## Start PostgreSQL

From this directory:

```powershell
docker compose up -d postgres
```

## Install and run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
py -m backend.cli init
py -m backend.cli seed-demo
py -m uvicorn backend.app:app --reload
```

The API is at `http://127.0.0.1:8000`. OpenAPI request docs are served at `/docs` by FastAPI; this is API documentation, not a project frontend. Set `DATABASE_URL` in `.env` to use another PostgreSQL instance.

## Main API routes

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Check API availability |
| `POST`, `GET` | `/hospitals` | Add/list hospitals |
| `POST`, `GET` | `/donors` | Add/list synthetic donors |
| `POST`, `GET` | `/organs` | Register/list organs, optionally filter by status |
| `POST`, `GET` | `/recipients` | Register/list recipients |
| `PUT` | `/hospital-distances` | Set directed hospital-to-hospital distance |
| `GET` | `/organs/{id}/matches` | List compatible recipients in priority order |
| `POST` | `/allocations/claim` | Atomically claim an organ for a recipient |
| `GET` | `/allocations` | List allocation decisions |
| `GET` | `/analytics` | Get simulation metrics |
| `GET` | `/events` | Read newest audit events (`limit` 1-1000) |
| `POST` | `/simulation/deadlines` | Expire overdue organs |
| `POST` | `/simulation/deadlock` | Run controlled cycle detection and resolution demo |
| `POST` | `/simulation/recover` | Reconcile state from committed allocation events |

## CLI simulations

```powershell
py -m backend.cli deadlock-demo
py -m backend.cli deadlines
py -m backend.cli recover
py -m backend.cli analytics
```

The SQL schema is in `schema.sql`; the app also applies it on startup. Keep `.env` private and use synthetic data only.
