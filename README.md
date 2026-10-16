# UltraByte Solutions

> Rules tell you what happened. UltraByte tells you why it matters.

Explainable alert triage for gaming investigators, covering fraud/AML and safer-play harm.
UltraByte flags unusual player activity, compares it against each player's own history, profile and peer group, and ranks who to review first. Every score breaks down into named factors with a reason and a source, and every investigator decision lands on an append-only audit trail.

**Built during ThunderHacks II, 14-16 Oct 2026 (Algoma University).** No code existed before the opening ceremony; see `BUILD-LOG.md` and the commit history.

**Data:** 100% SYNTHETIC. No real players, transactions, or sponsor data.

## Status

| Milestone | Scope | State |
|---|---|---|
| M0 | Skeleton, schema, synthetic seed, `/health`, `/reset` | done |
| M1 | Context score: 4 checks x 25 points, each with a reason and a source; STR / URGENT / Safer Gambling labels | done |
| M2 | Ranked queue; player page ("why 75?", reasons with sources, 6-month chart vs peer range, locations, highlighted evidence) | done |
| M3 | Escalate / Monitor / Dismiss with a note, saved to the append-only audit trail with a full score snapshot | done |
| S1 | Validation page: planted cases expected vs actual, Version 1.0 vs 2.0, false positives over the whole population | done |
| S2 | Suggested next step per alert, rule-based, with the rule shown (advice only; the investigator decides) | done |
| S3 | Dashboard by category: URGENT, STR candidates, context risk, Safer Gambling, Newly added (manual entry or import) | done |
| Case hand-off | Investigator escalates; compliance opens the player page and clicks **Mark as handling**, then **Mark resolved** (compliance role only, note optional). Two more append-only audit actions (`handling`, `resolve`); the case status is the latest decision-or-status row per player and is shown on the player page and in the Decided table (escalated, in progress, monitor, dismissed, resolved). Migration `006_case_status.sql` | done |
| Worklist split | Review queue = worklist: "Action required" (caught players with no recorded decision, most urgent first) and "Decided" (latest decision from the audit trail, with who and when). Overview = the same players grouped by team | done |
| Queue search | Search by name or player ID and filter chips (band High / Medium / Low; category URGENT, STR, Safer Gambling, Newly added) on the review queue, in the browser; players added during the session carry a NEW tag with their source | done |
| C1 | Network view: cards and payout bank accounts shared by more than one player | done |
| Import | Bring your own synthetic data: Excel template (players, transactions, sessions) or CSV; every row validated; sensitive columns rejected; load replaces or adds; scores recomputed | done |
| Manual entry | `/enter`: type one deposit or withdrawal (existing player, or a new one with a fictional name, bands and an occupation from the dataset list); the player is rescored at once and the page shows each check before and after, new labels and the suggested step; every entry is an audit event (`manual_entry`); `/reset` removes manually entered rows | done |
| Version 1.0 console | `/v1`: illustrative reconstruction of today's routine (threshold alert with no reason, separate history / profile / card-lookup screens, notes copied to a spreadsheet, nothing stored). Same data, not linked from Version 2.0. Replaced the Before / After split queue (D-2026-10-15-22) | done |
| Step counter | Badge on every page of both versions: one step = one click; typing not counted; separate counts for 1.0 and 2.0, kept in the browser only. Case H measured: 7 steps in 1.0, 2 in 2.0 | done |
| Rules | `/rules`: every threshold the two scores use, editable by a compliance operator; each save is a new append-only `rule_version` row with a required reason and an audit event listing before/after values; all players are rescored; each score snapshot records its rule version. Version 1 = team spec defaults | done |
| Safer Gambling score | Second score, 0-100, four checks x 25 (escalation of monthly deposits, night play, loss chasing, intensity), own band and ring, separate from the AML score; Safer Gambling band Medium or High puts the player in the queue and routes the suggestion to the Safer Gambling team | done |
| Sign-in | Operator sign-in with two roles: `investigator` (queue, decisions, manual entry, AI summary, rules read-only) and `compliance` (all of that plus editing rules). Accounts and the cookie secret come from the environment; sign-in and sign-out are audit events; the audit actor is the signed-in user. User menu top-right with a Profile page (account, session, own recent activity); the change-password form is a labelled mock-up | done |
| AI summary | Optional, behind `LLM_ENABLED`: a 3-sentence investigator summary written by Claude via an n8n webhook from the computed reasons only; checked before display; cached; written to the audit trail (`ai_summary`). The score never depends on it | done |

Menu: Daily work (Review queue with a to-do count, Overview, Audit trail) and Manage (Score rules, Manual entry, Import test data). Pages: `/` review queue (the investigator's inbox: With comment, To do, Escalated & monitor, Dismissed; a case leaves it once compliance responds and is tracked on Overview under In progress and Resolved) (`?mode=v2` for Version 2.0 alone), `/player/{id}`, `/enter`, `/rules`, `/about` (AI disclosure), `/profile`, `/dashboard` (Overview, incl. shared cards and bank accounts; `/network` redirects there), `/validation` (Version 1.0 vs 2.0, a demo button beside the step counter, not a menu item), `/import`, `/audit`, `/report` (case report: counts per status and category, handling time, all cases; `/report.csv` download, print-ready). Health: `/health`. Demo reset: `POST /reset`. Explanations sit behind the small "?" buttons so screens stay clean; abbreviations (STR, AML, FINTRAC) show their meaning on hover. Every form shows "Saving...", confirms with a green message, and carries a one-time token so a double click is never saved twice.

## Architecture

```
Browser -> Nginx (TLS) -> app container (FastAPI + Jinja, 127.0.0.1:3110)
                              |-- app/scoring/  explainable score (M1)
                              |-- app/audit/    append-only audit_event (M3)
                              |-- app/judge.py  judge input (one transaction -> rescore)
                              |-- app/llm/      optional AI summary, behind LLM_ENABLED (off by default)
                              |      '-- n8n webhook (header key) -> Anthropic Claude -> 3-sentence summary
                              '-- Postgres 16 (self-hosted, synthetic data only)
```

The core logic (scoring, audit, judge input) lives in this repo and needs no LLM. The AI summary is optional and
one-directional: the app sends only what the rules scorer already computed (score, band, check reasons, labels,
suggestion; no names, no raw transactions) to an n8n workflow, which asks Claude to reword it for an investigator.
Before display the app checks that every number in the reply appears in the input; otherwise, or if n8n or the
model is unavailable, the rule text is shown instead. The summary is cached per score snapshot and recorded in the
audit trail with the model name. n8n workflow: "UltraByte - AI case summary (THX)", 3 nodes (Webhook with header
auth -> Anthropic -> Respond).

## How the score works

Each player gets four checks, 0-25 points each, computed on the last 30 days (15 Sep - 14 Oct 2026):

| Check | Question | Points |
|---|---|---|
| Income fit | Do 30-day deposits fit the income band? | 0 below 25% of estimated monthly income, scaling to 25 at 100% |
| Own history | Is this a change for this player? | 0 below 2x the player's monthly average, scaling to 25 at 10x |
| Peers | Is this unusual for players of the same age band and income band? | 15 above the 95th percentile, 25 above the 99th; not scored when fewer than 20 peers |
| Location | Sessions from 3+ cities within 24 hours? | 25 |

Bands: High >= 50, Medium 25-49, Low < 25. Labels add no points but pin a player near the top:
**STR candidate** (deposits just under $10,000, minimal play before withdrawal, a card or bank account shared
with another player, payout to someone else's account), **URGENT** (unusual locations plus a new card or bank
account), **Safer Gambling** (deposits rising 4+ months in a row, or most sessions between midnight and 4 a.m.).
Every threshold lives in `app/scoring/config.py`.

**Version 1.0** in the demo is a simplified stand-in for a threshold rule (any single deposit of $10,000 or
more). It is not OLG's actual rule. The routine built around it in the `/v1` console (separate look-up screens, notes kept in a
spreadsheet) is the team's assumption of how an investigator works today; it has not been confirmed by a
current user and is labelled as a reconstruction on every screen.

## Results on the synthetic data (honest reading)

- The 10 planted cases (A-J, 11 players) were **designed by the team** to exercise each check. Catching them
  is a test that the logic does what it says, **not evidence of real-world performance**.
- On that set: Version 1.0 alerts on 2 players (one is the wealthy regular, a false alarm) and misses the
  $9,500 x3 structuring case. Version 2.0 catches all 9 risky players and clears both controls.
- False positives are reported over the **whole normal population**: 6 of 490 normal players reach Medium,
  none reach High, all through the peer check.

## Data model and governance choices

- `player`, `txn`, `session`: ~500 synthetic Ontario players, 15 Apr - 14 Oct 2026. The generator draws a
  hidden "actual income" inside each band to drive spending; only the band is stored.
- **Data minimization:** only age band, income band and home city are stored. No exact age, gender, ethnicity
  or other sensitive attributes. Peer group = age band x income band. Payout account holder names are never
  stored, only whether the holder matches the player.
- `audit_event` is **append-only**: a database trigger rejects UPDATE and DELETE. The demo-only `/reset` endpoint uses TRUNCATE to restore the seed, and logs a `reset` event.
- `planted_case` holds ground-truth labels for the planted cases. **The scorer never reads this table**; it is
  used only to measure Version 1.0 vs 2.0.
- The seed is deterministic (fixed RNG seed and fixed reference date), so every reset produces identical data.

## Demo data

`demo/UltraByte_demo_300_players.xlsx` holds 308 synthetic players with planted scenarios (see its README sheet). Import it with
mode **Add** so the 490 background players keep the peer check meaningful; **Reset demo data** removes it again. Regenerate
with `python demo/make_demo.py` (deterministic).

## Run locally

```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql://user:pass@localhost:5432/thx_ultrabyte
PSQL="psql $DATABASE_URL" scripts/migrate.sh db/migrations/001_init.sql apply
PSQL="psql $DATABASE_URL" scripts/migrate.sh db/migrations/002_k0v07_spec.sql apply
python -m db.seed.generate
uvicorn app.main:app --port 3110
scripts/smoke.sh http://127.0.0.1:3110
```

## Deploy

No CI and no secrets in the repo. `scripts/deploy.sh` calls a script on the server over SSH; that script pulls `main`, rebuilds the container and checks health. Credentials exist only as environment variables on the server (`.env`, never committed).

- v0.15.0 needs `db/migrations/006_case_status.sql` (adds two audit actions): `PSQL="docker exec -i ultrabyte-postgres psql -U ultrabyte_app -d thx_ultrabyte" bash scripts/migrate.sh db/migrations/006_case_status.sql apply` (use `bash`: a Windows checkout drops the execute bit). Applied on the demo VPS 2026-10-15 18:07. No data change, no reset needed.
- nginx in front of the app: `client_max_body_size 20m;` in the server block, or the Excel import (1.5 MB) is refused with 413.

## Known simplifications (disclosed)

- All data is synthetic and generated by `db/seed/generate.py`; the planted cases and their parameters are hand-chosen.
- Estimated income is the midpoint of the income band, not a real income figure.
- All locations are inside Ontario. Basis: AGCO Registrar's Standards for Internet Gaming, Standard 3.02 (games provided only
  within Ontario; operators detect and monitor player location). The app never blocks play by location: the location check
  only flags possible account takeover (several cities within hours) for review and step-up verification. An OLG mentor
  suggested residency is verified by ID at registration and travelling players should not be blocked (informal, not OLG policy).
- Equal weights by design: the four checks count 25 points each until they can be calibrated on real outcomes. The most
  serious signals do not depend on the score: FINTRAC red flags and account takeover add a label (STR candidate, URGENT)
  that pins the player near the top of the queue. No model is trained on the synthetic data, because it would only learn
  the patterns the team planted.
- Income and occupation are used where available. An operator that does not hold them loses the income-fit and peer
  inputs; own history, location, the labels and the Safer Gambling score still work.
- For URGENT the suggested action includes step-up verification (two-factor or an email check to the player). Sending that
  message is outside this prototype.
- Design feedback from an OLG mentor during the event (one panel, expected vs actual behaviour, plain-language
  explanations, optional income data) shaped these choices. It is informal guidance, not OLG policy.
- Suggested actions are fixed rules in `app/scoring/engine.py` (`suggest`); no LLM is involved in scoring, labels or suggestions.
- The AI summary (when `LLM_ENABLED=true`) is prose only; it cannot change a score, label or suggestion. Its number check
  is a safeguard against invented figures, not a guarantee of faithful wording; the computed reasons stay on screen beside it.
- Thresholds are operator defaults, not calibrated values. Version 1 is the team spec; calibration on real data is the
  operator's job, and the Rules page plus `rule_version` history exist so that job is auditable. Safer Gambling band
  Medium starts at 30 by default so that one marker alone (max 25) does not raise an alert.
- Safer Gambling markers (deposit trajectory, late-night play, chasing losses, frequency of play) follow the OLG brief's
  player-protection theme and commonly cited behavioural harm markers; the primary references are listed as a to-do for
  the team (lane d) and marked ASSUMED until verified.
- Judges: the live login page shows demo accounts while `DEMO_LOGINS` is set on the server. These are demo-only passwords for synthetic data, removed after judging.
- Sign-in is demo-grade: static accounts and passwords from `OPERATOR_ACCOUNTS`, an HMAC-signed cookie (8 h), no MFA, no
  SSO, no lockout. If `OPERATOR_ACCOUNTS` is unset the app runs without sign-in and says so in the sidebar.
- Manual entry: a typed deposit also creates a 30-minute session at the same city and time (so the location check can see
  it), and the same card "last 4" on two manually entered players counts as a shared card. New players get the id prefix `M-`;
  a fictional first and last name (optional, letters only) is stored as "First L." like the seed, and the occupation is picked from
  the seed's list for the income band. Manually entered rows are tagged `entry_source = 'manual'`.
- Import "replace" mode clears the audit trail together with the data (same demo-only path as reset); "add" mode keeps it.
- The demo date is fixed: "last 30 days" means 15 Sep - 14 Oct 2026, so the data never changes between resets.

## Assets and licences

- Team logo (`app/static/brand/team/`): a gem-tiled "U" mark with the "Ultra Byte Solutions" wordmark, generated by the
  team during the event with Google Gemini (AI-generated image, disclosed). The app uses the "U" mark cropped from it
  with a feathered edge; the wordmark in the app is text. The UI palette is sampled from the logo. Earlier SVG drafts ("Eight Bits") remain in `app/static/brand/` and are unused.
- No third-party images or icons. Python libraries: FastAPI, Uvicorn, Jinja2, psycopg (see `requirements.txt`).

## AI disclosure

AI coding assistants (Claude, Anthropic) were used during the event to help write code, the synthetic data generator and documentation. All design decisions were made by the team; all output was reviewed and tested by the team.

| Component | AI involvement |
|---|---|
| Scoring rules, thresholds, labels (`app/scoring/`) | Rules and thresholds chosen by the team from the OLG brief and FINTRAC indicators; code written with Claude's help |
| Synthetic data generator, planted cases | Scenarios designed by the team; code written with Claude's help |
| UI, templates, CSS | Written with Claude's help; layout decisions by the team |
| README, BUILD-LOG, docs | Drafted with Claude's help, edited by the team |
| Team logo | AI-generated image (Google Gemini), see Assets |
| AI case summary at runtime | Anthropic Claude via n8n, optional (`LLM_ENABLED`), prose only; labelled "AI-generated" on screen |
