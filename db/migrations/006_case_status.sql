-- Case hand-off between roles (owner 2026-10-15 17:32): two more append-only audit actions.
-- 'handling' = compliance has picked the escalated case up; 'resolve' = compliance closed it. The latest of
-- escalate / monitor / dismiss / handling / resolve per player is the case status; nothing is updated in place.
ALTER TABLE audit_event DROP CONSTRAINT audit_event_action_check;
ALTER TABLE audit_event ADD CONSTRAINT audit_event_action_check
    CHECK (action IN ('escalate','monitor','dismiss','note','reset','manual_entry','ai_summary','rule_change','login','logout','handling','resolve'));
