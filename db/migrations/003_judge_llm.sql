-- 003_judge_llm.sql - judge input (C) and AI summary (B). Owner decision D-2026-10-14-16 (HS4 opened 21:45 EDT).
-- All data is SYNTHETIC. Additive only: no data is changed or removed.

-- Where a row came from. NULL = synthetic seed or file import; 'judge' = typed in on /enter during the demo.
ALTER TABLE player  ADD COLUMN entry_source text;
ALTER TABLE txn     ADD COLUMN entry_source text;
ALTER TABLE session ADD COLUMN entry_source text;

-- Two new audit actions: a judge entry and an AI-generated summary (both append-only, like decisions).
ALTER TABLE audit_event DROP CONSTRAINT audit_event_action_check;
ALTER TABLE audit_event ADD CONSTRAINT audit_event_action_check
    CHECK (action IN ('escalate','monitor','dismiss','note','reset','manual_entry','ai_summary'));
