from psycopg.types.json import Jsonb

from .db import connection
from .matching import is_compatible, priority_score


def _event(conn, event_type, entity_type, entity_id=None, hospital_id=None, payload=None):
    conn.execute(
        "INSERT INTO allocation_events(event_type,entity_type,entity_id,hospital_id,payload) VALUES(%s,%s,%s,%s,%s)",
        (event_type, entity_type, entity_id, hospital_id, Jsonb(payload or {})),
    )


def create_hospital(name):
    with connection() as conn:
        row = conn.execute("INSERT INTO hospitals(name) VALUES(%s) RETURNING *", (name,)).fetchone()
        _event(conn, "HOSPITAL_CREATED", "hospital", row["hospital_id"], payload={"name": name})
        return row


def create_donor(name, blood_type):
    with connection() as conn:
        row = conn.execute("INSERT INTO donors(name,blood_type) VALUES(%s,%s) RETURNING *", (name, blood_type.upper())).fetchone()
        _event(conn, "DONOR_CREATED", "donor", row["donor_id"], payload={"blood_type": blood_type.upper()})
        return row


def create_organ(data):
    with connection() as conn:
        donor = conn.execute("SELECT blood_type FROM donors WHERE donor_id=%s", (data.donor_id,)).fetchone()
        if not donor:
            raise ValueError("Donor not found")
        if donor["blood_type"] != data.blood_type.upper():
            raise ValueError("Organ blood type must match its donor blood type")
        row = conn.execute(
            "INSERT INTO organs(donor_id,donor_hospital_id,organ_type,blood_type,expires_at) VALUES(%s,%s,%s,%s,now() + (%s * interval '1 second')) RETURNING *",
            (data.donor_id, data.donor_hospital_id, data.organ_type.strip(), data.blood_type.upper(), data.viability_seconds),
        ).fetchone()
        _event(conn, "ORGAN_REGISTERED", "organ", row["organ_id"], payload={"organ_type": row["organ_type"], "expires_at": row["expires_at"].isoformat()})
        return row


def create_recipient(data):
    with connection() as conn:
        row = conn.execute(
            "INSERT INTO recipients(name,organ_type,blood_type,urgency_score,waiting_days,hospital_id) VALUES(%s,%s,%s,%s,%s,%s) RETURNING *",
            (data.name.strip(), data.organ_type.strip(), data.blood_type.upper(), data.urgency_score, data.waiting_days, data.hospital_id),
        ).fetchone()
        _event(conn, "RECIPIENT_REGISTERED", "recipient", row["recipient_id"], row["hospital_id"])
        return row


def set_distance(data):
    with connection() as conn:
        conn.execute(
            "INSERT INTO hospital_distances(from_hospital_id,to_hospital_id,distance_km) VALUES(%s,%s,%s) ON CONFLICT(from_hospital_id,to_hospital_id) DO UPDATE SET distance_km=EXCLUDED.distance_km",
            (data.from_hospital_id, data.to_hospital_id, data.distance_km),
        )
        _event(conn, "DISTANCE_UPDATED", "hospital_distance", payload=data.model_dump())
    return {"status": "saved", **data.model_dump()}


def _distance(conn, organ_id, candidate_hospital_id):
    # If no donor-origin distance has been entered, use zero for a local/unspecified route.
    row = conn.execute(
        "SELECT COALESCE((SELECT distance_km FROM hospital_distances WHERE from_hospital_id=o.donor_hospital_id AND to_hospital_id=%s),0) AS km FROM organs o WHERE o.organ_id=%s",
        (candidate_hospital_id, organ_id),
    ).fetchone()
    return float(row["km"])


def ranked_recipients(organ_id):
    with connection() as conn:
        organ = conn.execute("SELECT * FROM organs WHERE organ_id=%s", (organ_id,)).fetchone()
        if not organ:
            raise ValueError("Organ not found")
        rows = conn.execute(
            "SELECT r.*,h.name AS hospital_name FROM recipients r JOIN hospitals h USING(hospital_id) WHERE r.active AND lower(r.organ_type)=lower(%s) AND r.blood_type IN ('O-','O+','A-','A+','B-','B+','AB-','AB+')",
            (organ["organ_type"],),
        ).fetchall()
        candidates = []
        for row in rows:
            if not is_compatible(organ["blood_type"], row["blood_type"]):
                continue
            distance = _distance(conn, organ_id, row["hospital_id"])
            candidates.append({**dict(row), "distance_km": distance, "priority_score": priority_score(row["urgency_score"], row["waiting_days"], distance)})
        return sorted(candidates, key=lambda r: (-r["priority_score"], r["waiting_days"], r["recipient_id"]))


def allocate(data):
    """Claim using a DB transaction and row-level lock; unique organ_id is final guard."""
    with connection() as conn:
        organ = conn.execute("SELECT * FROM organs WHERE organ_id=%s FOR UPDATE", (data.organ_id,)).fetchone()
        if not organ:
            raise ValueError("Organ not found")
        if organ["status"] != "AVAILABLE":
            _event(conn, "CLAIM_REJECTED", "organ", data.organ_id, data.hospital_id, {"reason": "organ is not available"})
            return {"allocated": False, "reason": "organ is not available"}
        if organ["expires_at"] <= conn.execute("SELECT now() AS now").fetchone()["now"]:
            conn.execute("UPDATE organs SET status='WASTED' WHERE organ_id=%s", (data.organ_id,))
            conn.execute("DELETE FROM resource_locks WHERE organ_id=%s", (data.organ_id,))
            _event(conn, "ORGAN_EXPIRED", "organ", data.organ_id, data.hospital_id)
            return {"allocated": False, "reason": "organ viability deadline passed"}
        recipient = conn.execute(
            "SELECT r.*,h.name AS hospital_name FROM recipients r JOIN hospitals h USING(hospital_id) WHERE r.recipient_id=%s AND r.active FOR SHARE OF r",
            (data.recipient_id,),
        ).fetchone()
        if not recipient:
            raise ValueError("Active recipient not found")
        if recipient["hospital_id"] != data.hospital_id:
            raise ValueError("Claiming hospital must match recipient's hospital")
        if recipient["organ_type"].lower() != organ["organ_type"].lower() or not is_compatible(organ["blood_type"], recipient["blood_type"]):
            _event(conn, "CLAIM_REJECTED", "organ", data.organ_id, data.hospital_id, {"reason": "recipient is not compatible", "recipient_id": data.recipient_id})
            return {"allocated": False, "reason": "recipient is not compatible"}
        # INSERT ... ON CONFLICT is an explicit resource-lock/mutex record. The organ
        # row lock serializes claims; this row provides visible lock ownership to the demo.
        lock = conn.execute(
            "INSERT INTO resource_locks(organ_id,hospital_id) VALUES(%s,%s) ON CONFLICT(organ_id) DO NOTHING RETURNING organ_id",
            (data.organ_id, data.hospital_id),
        ).fetchone()
        if not lock:
            _event(conn, "CLAIM_REJECTED", "organ", data.organ_id, data.hospital_id, {"reason": "resource lock already held"})
            return {"allocated": False, "reason": "resource lock already held"}
        allocation = conn.execute(
            "INSERT INTO allocations(organ_id,recipient_id,hospital_id,status,reason) VALUES(%s,%s,%s,'ALLOCATED',%s) RETURNING *",
            (data.organ_id, data.recipient_id, data.hospital_id, "Highest-ranked compatible active recipient; claim serialized by PostgreSQL row lock"),
        ).fetchone()
        conn.execute("UPDATE organs SET status='ALLOCATED' WHERE organ_id=%s", (data.organ_id,))
        conn.execute("UPDATE recipients SET active=FALSE WHERE recipient_id=%s", (data.recipient_id,))
        _event(conn, "ALLOCATION_COMMITTED", "allocation", allocation["allocation_id"], data.hospital_id, {"organ_id": data.organ_id, "recipient_id": data.recipient_id, "reason": allocation["reason"]})
        conn.execute("DELETE FROM resource_locks WHERE organ_id=%s", (data.organ_id,))
        return {"allocated": True, "allocation": allocation}


def process_deadlines():
    with connection() as conn:
        rows = conn.execute("UPDATE organs SET status='WASTED' WHERE status='AVAILABLE' AND expires_at<=now() RETURNING organ_id").fetchall()
        for row in rows:
            _event(conn, "ORGAN_EXPIRED", "organ", row["organ_id"])
        return {"expired_count": len(rows), "organ_ids": [r["organ_id"] for r in rows]}


def analytics():
    with connection() as conn:
        row = conn.execute("""SELECT
            (SELECT count(*) FROM organs) AS total_organs,
            (SELECT count(*) FROM allocations WHERE status='ALLOCATED') AS allocations,
            (SELECT count(*) FROM organs WHERE status='WASTED') AS wasted_organs,
            (SELECT count(*) FROM organs WHERE status='AVAILABLE') AS available_organs,
            COALESCE((SELECT avg(waiting_days) FROM recipients),0) AS average_waiting_days""").fetchone()
        total = row["total_organs"]
        return {**dict(row), "allocation_success_rate_percent": round(100 * row["allocations"] / total, 2) if total else 0.0, "wastage_rate_percent": round(100 * row["wasted_organs"] / total, 2) if total else 0.0}


def list_events(limit=100):
    with connection() as conn:
        return conn.execute("SELECT * FROM allocation_events ORDER BY event_id DESC LIMIT %s", (limit,)).fetchall()


def recover_from_event_log():
    """Reconcile organ/recipient state from committed allocation events after a simulated crash."""
    with connection() as conn:
        committed = conn.execute("SELECT payload FROM allocation_events WHERE event_type='ALLOCATION_COMMITTED' ORDER BY event_id").fetchall()
        recovered = 0
        for event in committed:
            payload = event["payload"]
            organ_id, recipient_id = payload.get("organ_id"), payload.get("recipient_id")
            if organ_id and recipient_id:
                conn.execute("UPDATE organs SET status='ALLOCATED' WHERE organ_id=%s AND status<>'ALLOCATED'", (organ_id,))
                conn.execute("UPDATE recipients SET active=FALSE WHERE recipient_id=%s", (recipient_id,))
                recovered += 1
        _event(conn, "RECOVERY_COMPLETED", "system", payload={"allocation_events_replayed": recovered})
        return {"replayed_allocations": recovered, "status": "recovery completed"}


def deadlock_demo():
    """Create a deterministic wait-for cycle and return the victim selected to break it."""
    # Graph: H1 holds R1 and waits R2; H2 holds R2 and waits R1. DFS detects cycle.
    holds = {"Hospital-1": "Resource-1", "Hospital-2": "Resource-2"}
    waits = {"Hospital-1": "Resource-2", "Hospital-2": "Resource-1"}
    owners = {resource: hospital for hospital, resource in holds.items()}
    graph = {hospital: owners.get(resource) for hospital, resource in waits.items()}
    visited, active, cycle = set(), set(), []

    def visit(node, path):
        nonlocal cycle
        if node in active:
            cycle = path[path.index(node):] + [node]
            return True
        if node in visited:
            return False
        visited.add(node); active.add(node)
        nxt = graph.get(node)
        if nxt and visit(nxt, path + [nxt]):
            return True
        active.remove(node)
        return False

    for hospital in graph:
        if visit(hospital, [hospital]):
            break
    victim = cycle[-2] if cycle else None
    return {"deadlock_detected": bool(cycle), "wait_for_cycle": cycle, "resolution": f"Abort {victim} request and release its held resource" if victim else "No deadlock"}
