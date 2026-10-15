-- 005_auth.sql - operator login (D-2026-10-15-20). Additive: audit trail records login and logout.
ALTER TABLE audit_event DROP CONSTRAINT audit_event_action_check;
ALTER TABLE audit_event ADD CONSTRAINT audit_event_action_check
    CHECK (action IN ('escalate','monitor','dismiss','note','reset','manual_entry','ai_summary','rule_change','login','logout'));
