-- 001_init.sql - UltraByte core schema (M0)
-- All data in this database is SYNTHETIC. No real players or transactions.
-- Data minimization (K0 §3): no gender, ethnicity or other sensitive attributes.
-- Peer group uses age_band, income_band and region only.

CREATE TABLE player (
    id            text PRIMARY KEY,
    display_name  text        NOT NULL,             -- synthetic name
    occupation    text        NOT NULL,
    income_band   text        NOT NULL CHECK (income_band IN ('<30k','30-60k','60-100k','100-200k','>200k')),
    age_band      text        NOT NULL CHECK (age_band IN ('19-24','25-34','35-49','50-64','65+')),
    region        text        NOT NULL,
    peer_segment  text        NOT NULL,             -- age_band|income_band|region
    synthetic     boolean     NOT NULL DEFAULT true CHECK (synthetic),
    created_at    timestamptz NOT NULL
);

CREATE TABLE txn (
    id                  bigserial PRIMARY KEY,
    player_id           text          NOT NULL REFERENCES player(id),
    ts                  timestamptz   NOT NULL,
    type                text          NOT NULL CHECK (type IN ('deposit','withdrawal','withdrawal_reversal','wager','win')),
    amount              numeric(12,2) NOT NULL CHECK (amount > 0),
    method              text          NOT NULL CHECK (method IN ('debit','credit','e_transfer','cash_cage','prepaid','wallet')),
    method_fingerprint  text,          -- hashed instrument id (synthetic); used by C1 network view
    location_region     text          NOT NULL,
    device_id           text          -- synthetic device id; used by C1 network view
);
CREATE INDEX txn_player_ts ON txn (player_id, ts);
CREATE INDEX txn_fingerprint ON txn (method_fingerprint);
CREATE INDEX txn_device ON txn (device_id);

CREATE TABLE session (
    id          bigserial PRIMARY KEY,
    player_id   text          NOT NULL REFERENCES player(id),
    start_ts    timestamptz   NOT NULL,
    end_ts      timestamptz   NOT NULL CHECK (end_ts >= start_ts),
    net_result  numeric(12,2) NOT NULL   -- wins minus wagers for the session
);
CREATE INDEX session_player_start ON session (player_id, start_ts);

-- Investigator decisions. Append-only: UPDATE and DELETE are rejected by trigger.
-- The demo /reset endpoint uses TRUNCATE to restore the seed; this is disclosed in README.
CREATE TABLE audit_event (
    id              bigserial PRIMARY KEY,
    ts              timestamptz NOT NULL DEFAULT now(),
    actor           text        NOT NULL,
    player_id       text        REFERENCES player(id),
    action          text        NOT NULL CHECK (action IN ('escalate','monitor','dismiss','note','reset')),
    note            text,
    score_snapshot  jsonb       -- full score breakdown at decision time, so the decision can be reconstructed
);

CREATE FUNCTION audit_event_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_event is append-only (% rejected)', TG_OP;
END;
$$;

CREATE TRIGGER audit_event_no_update_delete
    BEFORE UPDATE OR DELETE ON audit_event
    FOR EACH ROW EXECUTE FUNCTION audit_event_append_only();

-- Ground-truth labels for the 10 planted scenarios.
-- The scorer never reads this table; it is used only by the validation panel (S1).
CREATE TABLE planted_case (
    case_no            int  NOT NULL,
    player_id          text NOT NULL REFERENCES player(id),
    label              text NOT NULL,
    expected           text NOT NULL CHECK (expected IN ('flag','no_flag')),
    expected_category  text CHECK (expected_category IN ('fraud_aml','harm')),
    source_ref         text,
    PRIMARY KEY (case_no, player_id)
);
