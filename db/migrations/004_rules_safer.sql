-- 004_rules_safer.sql - operator-owned rule thresholds (versioned) and Safer Gambling score.
-- Owner decision D-2026-10-15-19. All data is SYNTHETIC. Additive only.

-- Every change to a threshold is a new row; rows are never updated or deleted (same pattern as audit_event).
CREATE TABLE rule_version (
    id          serial PRIMARY KEY,
    created_at  timestamptz NOT NULL DEFAULT now(),
    actor       text        NOT NULL,
    note        text        NOT NULL,          -- why the operator changed it
    rules       jsonb       NOT NULL           -- full set of thresholds in force from this version on
);

CREATE FUNCTION rule_version_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'rule_version is append-only (% rejected)', TG_OP;
END;
$$;
CREATE TRIGGER rule_version_no_update_delete
    BEFORE UPDATE OR DELETE ON rule_version
    FOR EACH ROW EXECUTE FUNCTION rule_version_append_only();

-- New audit action for a threshold change.
ALTER TABLE audit_event DROP CONSTRAINT audit_event_action_check;
ALTER TABLE audit_event ADD CONSTRAINT audit_event_action_check
    CHECK (action IN ('escalate','monitor','dismiss','note','reset','manual_entry','ai_summary','rule_change'));

-- Version 1 = the team spec (IN-07) defaults, so the first operator change becomes version 2.
INSERT INTO rule_version (actor, note, rules) VALUES ('system', 'Version 1: team spec defaults (IN-07)', '{"income_fit_floor": 0.25, "income_fit_span": 0.75, "history_floor": 2.0, "history_span": 8.0, "history_min_base": 50.0, "peer_p95": 0.95, "peer_p99": 0.99, "peer_min_group": 20, "location_cities": 3, "location_hours": 24, "band_medium": 25, "band_high": 50, "structuring_low": 9000, "structuring_high": 9999.99, "structuring_min": 2, "minimal_play_ratio": 0.1, "v1_threshold": 10000, "sg_escalating_months": 4, "sg_night_share": 0.6, "sg_night_min_sessions": 3, "sg_chase_minutes": 60, "sg_chase_count": 3, "sg_days_played": 20, "sg_band_medium": 30, "sg_band_high": 50}');
