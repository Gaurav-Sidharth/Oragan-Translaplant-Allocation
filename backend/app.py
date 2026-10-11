"""HTTP API for the organ allocation simulation. No user interface is included."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from psycopg.errors import UniqueViolation, ForeignKeyViolation

from .db import initialize_schema
from . import services
from .schemas import ClaimIn, DistanceIn, DonorIn, HospitalIn, OrganIn, RecipientIn


@asynccontextmanager
async def lifespan(_app):
    initialize_schema()
    yield


app = FastAPI(title="Organ Allocation Simulation API", version="1.0.0", lifespan=lifespan)


def run(call, *args):
    try:
        return call(*args)
    except (ValueError, UniqueViolation, ForeignKeyViolation) as exc:
        raise HTTPException(status_code=409 if not isinstance(exc, ValueError) else 400, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "ok", "database": "PostgreSQL"}


@app.post("/hospitals", status_code=201)
def add_hospital(data: HospitalIn):
    return run(services.create_hospital, data.name.strip())


@app.get("/hospitals")
def hospitals():
    from .db import connection
    with connection() as conn:
        return conn.execute("SELECT * FROM hospitals ORDER BY hospital_id").fetchall()


@app.post("/donors", status_code=201)
def add_donor(data: DonorIn):
    return run(services.create_donor, data.name.strip(), data.blood_type)


@app.get("/donors")
def donors():
    from .db import connection
    with connection() as conn:
        return conn.execute("SELECT * FROM donors ORDER BY donor_id").fetchall()


@app.post("/organs", status_code=201)
def add_organ(data: OrganIn):
    return run(services.create_organ, data)


@app.get("/organs")
def organs(status: str | None = Query(default=None, pattern="^(AVAILABLE|ALLOCATED|WASTED)$")):
    from .db import connection
    with connection() as conn:
        if status:
            return conn.execute("SELECT * FROM organs WHERE status=%s ORDER BY expires_at", (status,)).fetchall()
        return conn.execute("SELECT * FROM organs ORDER BY expires_at").fetchall()


@app.post("/recipients", status_code=201)
def add_recipient(data: RecipientIn):
    return run(services.create_recipient, data)


@app.get("/recipients")
def recipients(active: bool | None = None):
    from .db import connection
    with connection() as conn:
        if active is None:
            return conn.execute("SELECT r.*,h.name AS hospital_name FROM recipients r JOIN hospitals h USING(hospital_id) ORDER BY recipient_id").fetchall()
        return conn.execute("SELECT r.*,h.name AS hospital_name FROM recipients r JOIN hospitals h USING(hospital_id) WHERE active=%s ORDER BY recipient_id", (active,)).fetchall()


@app.put("/hospital-distances")
def update_distance(data: DistanceIn):
    return run(services.set_distance, data)


@app.get("/organs/{organ_id}/matches")
def matches(organ_id: int):
    return run(services.ranked_recipients, organ_id)


@app.post("/allocations/claim")
def claim(data: ClaimIn):
    return run(services.allocate, data)


@app.get("/allocations")
def allocations():
    from .db import connection
    with connection() as conn:
        return conn.execute("SELECT a.*,o.organ_type,r.name AS recipient_name,h.name AS hospital_name FROM allocations a JOIN organs o USING(organ_id) JOIN recipients r USING(recipient_id) JOIN hospitals h USING(hospital_id) ORDER BY allocated_at DESC").fetchall()


@app.get("/analytics")
def get_analytics():
    return services.analytics()


@app.get("/events")
def events(limit: int = Query(default=100, ge=1, le=1000)):
    return services.list_events(limit)


@app.post("/simulation/deadlock")
def simulate_deadlock():
    result = services.deadlock_demo()
    from .db import connection
    from .services import _event
    with connection() as conn:
        _event(conn, "DEADLOCK_DETECTED" if result["deadlock_detected"] else "NO_DEADLOCK", "system", payload=result)
    return result


@app.post("/simulation/deadlines")
def process_deadlines():
    return services.process_deadlines()


@app.post("/simulation/recover")
def recover():
    return services.recover_from_event_log()
