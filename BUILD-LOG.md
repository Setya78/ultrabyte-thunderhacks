# BUILD-LOG - UltraByte (ThunderHacks II)

Times are EDT (UTC-4) unless marked. VPS clock = WIB (UTC+7).

| Time (EDT) | Item | Status | Note |
|---|---|---|---|
| 2026-10-14 18:03 | R1 repo | DONE | Repo `Setya78/ultrabyte-thunderhacks` created after opening (private) |
| 2026-10-14 18:12 | Infra check (external) | DONE | DNS 103.103.20.38, TLS valid to 2027-01-10, 301 redirect, placeholder 200, 5434/5678 closed from internet. `docker ps` on VPS pending (operator) |
| 2026-10-14 18:13 | Infra check (VPS, operator) | DONE | ultrabyte-postgres healthy, n8n up, ultrabyte_net isolated, 5434 on 127.0.0.1 only. Port 3100 taken by a non-UltraByte service (out of scope, not modified); 3110/3120/8010 free |

## Decisions (owner, sprint log)

| ID | Time (EDT) | Decision |
|---|---|---|
| D-2026-10-14-07 | 18:14 | App port 3110, bound to 127.0.0.1 only (reached via Nginx) |
| D-2026-10-14-08 | 18:14 | Primary demo = live URL; localhost = fallback (K0 §6 supersedes Runbook R5 "deploy = Could") |
| D-2026-10-14-09 | 18:14 | VPS pulls the private repo with a read-only deploy key; revoked at teardown |
| D-2026-10-14-10 | 18:14 | Schema as `db/migrations/001_init.sql`, gate pattern: dry-run BEGIN..ROLLBACK -> apply --single-transaction -> verify |
