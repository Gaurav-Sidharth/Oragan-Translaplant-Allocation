CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS donors (
    donor_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    blood_type TEXT NOT NULL CHECK (blood_type IN ('O-','O+','A-','A+','B-','B+','AB-','AB+')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS organs (
    organ_id BIGSERIAL PRIMARY KEY,
    donor_id BIGINT NOT NULL REFERENCES donors(donor_id),
    organ_type TEXT NOT NULL,
    blood_type TEXT NOT NULL CHECK (blood_type IN ('O-','O+','A-','A+','B-','B+','AB-','AB+')),
    donor_hospital_id BIGINT REFERENCES hospitals(hospital_id),
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE','ALLOCATED','WASTED')),
    CHECK (expires_at > available_at)
);
CREATE TABLE IF NOT EXISTS recipients (
    recipient_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    organ_type TEXT NOT NULL,
    blood_type TEXT NOT NULL CHECK (blood_type IN ('O-','O+','A-','A+','B-','B+','AB-','AB+')),
    urgency_score SMALLINT NOT NULL CHECK (urgency_score BETWEEN 1 AND 10),
    waiting_days INTEGER NOT NULL DEFAULT 0 CHECK (waiting_days >= 0),
    hospital_id BIGINT NOT NULL REFERENCES hospitals(hospital_id),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS hospital_distances (
    from_hospital_id BIGINT NOT NULL REFERENCES hospitals(hospital_id),
    to_hospital_id BIGINT NOT NULL REFERENCES hospitals(hospital_id),
    distance_km NUMERIC(10,2) NOT NULL CHECK (distance_km >= 0),
    PRIMARY KEY (from_hospital_id, to_hospital_id)
);
CREATE TABLE IF NOT EXISTS allocations (
    allocation_id BIGSERIAL PRIMARY KEY,
    organ_id BIGINT NOT NULL UNIQUE REFERENCES organs(organ_id),
    recipient_id BIGINT NOT NULL REFERENCES recipients(recipient_id),
    hospital_id BIGINT NOT NULL REFERENCES hospitals(hospital_id),
    status TEXT NOT NULL CHECK (status IN ('ALLOCATED','REJECTED')),
    reason TEXT NOT NULL,
    allocated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS resource_locks (
    organ_id BIGINT PRIMARY KEY REFERENCES organs(organ_id) ON DELETE CASCADE,
    hospital_id BIGINT NOT NULL REFERENCES hospitals(hospital_id),
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS allocation_events (
    event_id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id BIGINT,
    hospital_id BIGINT REFERENCES hospitals(hospital_id),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_recipients_match_priority
    ON recipients (organ_type, blood_type, urgency_score DESC);
CREATE INDEX IF NOT EXISTS idx_organs_available_deadline
    ON organs (status, expires_at) WHERE status = 'AVAILABLE';
CREATE INDEX IF NOT EXISTS idx_events_entity_time ON allocation_events (entity_type, entity_id, event_id);
CREATE INDEX IF NOT EXISTS idx_allocations_time ON allocations (allocated_at DESC);

-- Enforce append-only audit history for application roles. The table owner can still
-- maintain the schema; normal API operations only insert and select event rows.
CREATE OR REPLACE FUNCTION reject_allocation_event_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'allocation_events is append-only';
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS allocation_events_append_only ON allocation_events;
CREATE TRIGGER allocation_events_append_only
    BEFORE UPDATE OR DELETE ON allocation_events
    FOR EACH ROW EXECUTE FUNCTION reject_allocation_event_mutation();
