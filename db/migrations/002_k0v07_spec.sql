-- 002_k0v07_spec.sql - align schema with the team spec (K0 v0.7 / IN-07).
-- All data is SYNTHETIC. This migration clears the M0 seed (synthetic) because band values change.
-- Data minimization: still bands only (no exact age, gender or ethnicity); account holder names are
-- never stored, only whether the payout account holder matches the player (boolean).

TRUNCATE audit_event, planted_case, txn, session, player RESTART IDENTITY;

-- Bands from the team spec. Age bands start at 19 (Ontario minimum gambling age).
ALTER TABLE player DROP CONSTRAINT player_income_band_check;
ALTER TABLE player DROP CONSTRAINT player_age_band_check;
ALTER TABLE player ADD CONSTRAINT player_income_band_check
    CHECK (income_band IN ('<20k','20-50k','50-100k','100-200k','200k+'));
ALTER TABLE player ADD CONSTRAINT player_age_band_check
    CHECK (age_band IN ('19-29','30-44','45-64','65+'));
COMMENT ON COLUMN player.region IS 'Home city (Ontario)';
COMMENT ON COLUMN player.peer_segment IS 'age_band|income_band';

-- Sessions carry where they were played from (location check d).
ALTER TABLE session ADD COLUMN location_region text;
ALTER TABLE session ADD COLUMN device_id text;
UPDATE session SET location_region = 'unknown' WHERE location_region IS NULL;
ALTER TABLE session ALTER COLUMN location_region SET NOT NULL;

-- Funding and payout instruments (synthetic fingerprints) for STR labels and URGENT.
ALTER TABLE txn ADD COLUMN method_last4 text;            -- masked display only, e.g. '4417'
ALTER TABLE txn ADD COLUMN payout_account text;          -- withdrawal destination fingerprint
ALTER TABLE txn ADD COLUMN payout_holder_match boolean;  -- false = account in another person's name
CREATE INDEX txn_payout_account ON txn (payout_account);

-- Planted cases are now lettered A-J.
DROP TABLE planted_case;
CREATE TABLE planted_case (
    case_id            text NOT NULL,
    player_id          text NOT NULL REFERENCES player(id),
    label              text NOT NULL,
    expected           text NOT NULL CHECK (expected IN ('flag','no_flag')),
    expected_category  text CHECK (expected_category IN ('fraud_aml','harm')),
    source_ref         text,
    PRIMARY KEY (case_id, player_id)
);
