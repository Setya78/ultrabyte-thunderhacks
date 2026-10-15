# BUILD-LOG - UltraByte (ThunderHacks II)

Times are EDT (UTC-4) unless marked. VPS clock = WIB (UTC+7).

| Time (EDT) | Item | Status | Note |
|---|---|---|---|
| 2026-10-14 18:03 | R1 repo | DONE | Repo `Setya78/ultrabyte-thunderhacks` created after opening (private) |
| 2026-10-14 18:12 | Infra check (external) | DONE | DNS 103.103.20.38, TLS valid to 2027-01-10, 301 redirect, placeholder 200, 5434/5678 closed from internet. `docker ps` on VPS pending (operator) |
| 2026-10-14 18:13 | Infra check (VPS, operator) | DONE | ultrabyte-postgres healthy, n8n up, ultrabyte_net isolated, 5434 on 127.0.0.1 only. Port 3100 taken by a non-UltraByte service (out of scope, not modified); 3110/3120/8010 free |

## Decisions (owner, sprint log)

D-2026-10-14-07 = K0 v0.7 (team spec IN-07 adopted), logged in the project decision log at 19:12 EDT. Sprint IDs below were renumbered at 19:58 EDT to avoid a clash with it (they were first written as -07 to -10).

| ID | Time (EDT) | Decision |
|---|---|---|
| D-2026-10-14-08 | 18:14 | App port 3110, bound to 127.0.0.1 only (reached via Nginx) |
| D-2026-10-14-09 | 18:14 | Primary demo = live URL; localhost = fallback (K0 §6 supersedes Runbook R5 "deploy = Could") |
| D-2026-10-14-10 | 18:14 | VPS pulls the private repo with a read-only deploy key; revoked at teardown |
| D-2026-10-14-11 | 18:14 | Schema as `db/migrations/001_init.sql`, gate pattern: dry-run BEGIN..ROLLBACK -> apply --single-transaction -> verify |
| D-2026-10-14-12 | 19:55 | Peer check scores only when the peer group has at least 20 other players (amendment to IN-07 formula). Measured: normal players at Medium or above 14/490 -> 6/490; all planted cases unchanged |

## Build log (continued)

| Time (EDT) | Item | Status | Note |
|---|---|---|---|
| 2026-10-14 18:20 | Commit 1 pushed | DONE | `chore(M0): repo init, README stub, BUILD-LOG` |
| 2026-10-14 18:22 | M0 skeleton | DONE (local) | FastAPI + Jinja, `/health`, empty queue, `POST /reset`; `001_init.sql` (gate pattern passed on PG16); deterministic synthetic seed: 201 players, 16,430 txns, 3,350 sessions, 10 planted cases; audit_event DELETE rejected by trigger; smoke 3/3 OK. Naive V1 "$10k deposit" rule flags A (7x, false positive), B and cash-through, misses structuring. Live deploy pending |
| 2026-10-14 18:31 | Migration 001 on VPS | DONE | Gate pattern: dry-run OK, apply, verify 5 tables (operator) |
| 2026-10-14 18:3x | Commit 2 | NOTE | Commit message typed as `eat(M0): ...` (missing "f"). Left as is: fixing it needs a force-push (HS3) |
| 2026-10-14 19:40 | M0 rework to K0 v0.7 | DONE (local) | `002_k0v07_spec.sql` (IN-07 bands, session location, payout account + holder-match flag, planted cases A-J); seed: 501 players (490 + 11 planted), 62,364 txns, 11,975 sessions, Ontario only. Age bands start at 19 (Ontario minimum age) instead of 18 |
| 2026-10-14 19:58 | M1 explainable score | DONE (local) | 4 checks x 25 + labels STR / URGENT / Safer Gambling, every point with reason + source, scorer never reads planted_case. Planted: 9/9 risky caught, controls E and I cleared; V1 flags E and H only, misses G. Differences vs IN-07 table: A 40 (peer 15, G is in the same peer group), D 40 Medium + URGENT, P-6011 15 Low + STR. Normal population: 6/490 Medium, 0 High |
| 2026-10-14 19:58 | M2 part 1 | DONE (local) | Ranked queue (URGENT, then STR, then score), 4-part bar with text labels, Version 1.0 / 2.0 switch. Player page next |
| 2026-10-14 20:03 | Live deploy M0+M1 | DONE | Migration 002 on VPS (gate OK), container `ultrabyte-app` on 127.0.0.1:3110 (not reachable from internet, verified), Nginx `location /` -> proxy (backup in /opt/ultrabyte, `nginx -t` OK), app.jagacash.com still 307. Live smoke 3/3 OK on https://ultrabyte.denysetya.com; live V1 list = P-5120, P-8104. **Checkpoint Wed 21:30 met at 20:04** |
| 2026-10-14 20:10 | M2 player page | DONE (local) | "Why 75?" with 4 checks, reasons and sources; labels with sources; 6-month deposit chart vs peer 10th-90th percentile; last-30-day deposits/withdrawals with evidence rows highlighted; locations; Version 1.0 note when the old rule also fired. Checked at desktop and phone width |
| 2026-10-14 20:10 | M3 decisions + audit | DONE (local) | Escalate / Monitor / Dismiss + note -> `audit_event` INSERT with full score snapshot; per-player trail and `/audit` page. Verified: UPDATE on audit_event rejected by trigger. Actor = "investigator (demo)" (no auth, disclosed). **All Musts M0-M3 built** |
| 2026-10-14 20:20 | S1 validation | DONE (local) | `/validation`: V1 caught 1/9 risky, flagged 1/2 controls; V2 caught 9/9, flagged 0/2; background players in V2 queue 6/490 (0 High), listed on the page; "caught" definition printed |
| 2026-10-14 20:22 | Logo "Eight Bits" | DONE (local), choice pending | 2 variants + mono + favicon in `app/static/brand/`; variant 1 wired as default. Owner picks at the end (owner: logo last) |
| 2026-10-14 20:24 | S2 suggested action | DONE (local) | Rule-based `suggest()`: URGENT -> Fraud escalate; STR -> STR review; High or Medium with spend >= income -> AML source of funds; Medium + Safer label -> Safer Gambling; else monitor/dismiss. Rule shown with each suggestion. LLM not used |
| 2026-10-14 20:26 | S3 dashboard | DONE (local) | `/dashboard`: URGENT 1, STR 5, context risk 9, Safer Gambling 7 (players can be in several groups) |
| 2026-10-14 20:28 | C1 network | DONE (local) | `/network`: 2 shared instruments (card ending 4417, one payout account), both only P-6011 + P-6012; no other links in the data |
| 2026-10-14 20:30 | Commit messages | NOTE | Two commits landed as `eat(...)` (first letter dropped when typed in GitHub Desktop). History left as is (no force-push, HS3) |
| 2026-10-14 20:25 | Live deploy S1-C1 | DONE | v0.6.0-c1 live; smoke 3/3; all pages 200; live /validation shows V2 9/9, 0/2, 6/490, 15/15 (matches local). **All Must + Should + Could built; app ready for team feedback (Thu 13:00 checkpoint met Wed evening)** |
| 2026-10-14 20:34 | UI redesign v0.7.0 | DONE (local) | Owner: "too much text, not app-like, make it futuristic". Investigator console: dark ink base, sidebar nav, score as a 4-arc ring (one arc per check), KPI tiles, prose shortened. Kept: text on every risk label (never colour alone), synthetic-data badge on every page, all reasons + sources. Font Manrope via Google Fonts with system fallback |
| D-2026-10-14-13 | 20:40 | HS4 raised by owner: add "Import data" (bring your own synthetic Excel/CSV). Owner locked: via app only, no n8n. n8n webhook path = next step in pitch, not built |
| 2026-10-14 20:52 | Import data v0.8.0 | DONE (local) | `/import`: Excel template (3 sheets + README), upload .xlsx/.csv, per-row validation (bands, types, dates in window, unknown ids), forbidden sensitive columns rejected, replace/add modes, audit event, rescore. New dependency openpyxl. Verified: template loads both modes, forbidden column rejected, reset restores seed (UBP-29) |
| 2026-10-14 21:24 | Live deploy v0.8.0 | DONE | UI console + Import live. smoke.sh badge check updated for the new UI (case-insensitive, no early pipe close); live smoke 3/3; template download + file check via live URL OK |
| D-2026-10-14-14 | 21:25 | Owner: team logo (gem-tiled "U", AI-generated with Gemini, `03_inputs/`) is final. Supersedes logo direction A "Eight Bits" (D-2026-10-14-02). App uses the cropped U mark (header + favicon) with a plain-text wordmark; SVG drafts kept, unused. AI-generated asset disclosed in README |
| 2026-10-14 21:28 | Logo final | DONE (local) | `app/static/brand/team/`: mark 512/192/64/48 PNG (rounded), full logo 640 JPG. Mark copied to project `01_artefacts/` |
