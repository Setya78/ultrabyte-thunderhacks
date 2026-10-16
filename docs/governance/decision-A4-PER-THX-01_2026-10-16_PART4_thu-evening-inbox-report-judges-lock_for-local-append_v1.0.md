> Mirror for preflight discoverability. Not authoritative. Owner of record: `decision-A4-PER-THX-01.md`.
> Shard PART4 for local append. Covers Thu 15 Oct 18:53 to Fri 16 Oct 00:45 EDT. Sprint detail rows live in repo `BUILD-LOG.md` (PI §3.6).

## D-2026-10-15-29 — Report page after the D-27 lock (HS4, owner)

**Decision / Keputusan:** [EN] Add a read-only Case report page (`/report`, `/report.csv`): counts per status, category × status, handling time, all-cases table, CSV and print. No new table, no migration. / [ID] Tambah halaman Report read-only: jumlah per status, kategori × status, waktu penanganan, tabel semua kasus, CSV dan print. Tanpa tabel baru, tanpa migrasi.
**Trigger / Pemicu:** Owner 19:28 "fitur report berapa yang to do, in handling dan resolve". Agent raised HS4 (feature after "no new features" lock D-27) with 3 options; owner chose "Report page + CSV".
**Framework / Kerangka:** PI §3.4 HS4; Winning Bar §4.1b #3 (governance layer demoable).
**Anchor / Jangkar:** P4 (owner decided, logged), P6 (audit trail is the only source), P7 (synthetic data, CSV carries a SYNTHETIC column).
**Classification:** INTERNAL
**Artefacts:** repo `app/templates/report.html` (NEW), `app/main.py`, `app/audit/log.py` (`case_timeline()`), `app/static/app.css`, `README.md`, `BUILD-LOG.md` (D-29 + 19:45).
**Verification / Verifikasi:**
  - Report code deployed — VERIFIED-AGAINST-SoR (live `/health` = 0.16.2-judges 23:05, a later version that contains it; owner deploy log 22:56)
  - Report numbers correct — VERIFIED locally only (16 cases = 16 rows; 1.0 h / 2.0 h matched by hand). Live `/report` page view — ASSUMED → verify-by: SoR=open live `/report` signed in, counts add up to rows; agent=A4-PER-THX-01; by=Fri 09:00
**Open items / Item terbuka:** none.
**Next / Lanjutan:** Report is scene 8 of the video script.

## D-2026-10-15-30 — Demo sign-in shown on the login page for judges (owner)

**Decision / Keputusan:** [EN] Show demo accounts (investigator, compliance) with their passwords on `/login`, driven by env `DEMO_LOGINS` so no password is in the public repo; remove the variable after judging. / [ID] Tampilkan akun demo di halaman login lewat env `DEMO_LOGINS`; password tidak masuk repo publik; hapus variabel setelah judging.
**Trigger / Pemicu:** Owner 22:50 "juri gak bisa akses jika gak dikasih"; password given by owner in chat.
**Framework / Kerangka:** PI §3.4 HS2 (credentials) weighed: demo-only passwords, synthetic data, owner decision.
**Anchor / Jangkar:** P4, P5 (risk stated: anyone can sign in as compliance, change rules, reset data), P7.
**Classification:** INTERNAL (password not written in any governance file)
**Artefacts:** repo `app/templates/login.html`, `app/main.py` (`demo_logins()`), `app/static/app.css`, `.env.example`, `README.md`, `BUILD-LOG.md` (D-30 + 23:00). VPS `.env` line added by owner.
**Verification / Verifikasi:**
  - Live login shows the demo box — VERIFIED-AGAINST-SoR (curl `/login` contains `class="demologin"` 23:05; owner screenshot 23:05)
  - Sign-in with the demo accounts works on live — ASSUMED → verify-by: SoR=owner clicks investigator → Sign in on live; agent=A4-PER-THX-01; by=Fri 09:00
**Open items / Item terbuka:** remove `DEMO_LOGINS` after judging (UBP-27 teardown).
**Next / Lanjutan:** Reset demo data + check Score rules right before the pitch.

## D-2026-10-15-31 — UI restructure from owner review (owner choices)

**Decision / Keputusan:** [EN] (1) Review queue = investigator inbox: With comment, To do, Escalated & monitor, Dismissed; to-do count in the menu. (2) A case leaves the queue once compliance responds; Overview gains In progress and Resolved groups. (3) Open cases with a comment pinned on top. (4) Overview: explanations behind "?", search, equal-size cards. (5) Shared cards & accounts moves into Overview. (6) Menu = Daily work / Manage; Validation leaves the menu as a "Version 1.0 vs 2.0" button. / [ID] Enam perubahan UI dari review owner, semua pilihan owner lewat pertanyaan langsung.
**Trigger / Pemicu:** Owner messages 18:53–19:23 with screenshots; AskUserQuestion answers 19:00 (shared cards → Overview; 2 groups + Validation button), 19:10 (pin comments on top).
**Framework / Kerangka:** Scope = rework of existing screens, not new data or logic; treated as within the D-27 "fixes" lane. Report (new page) handled separately as HS4 (D-29).
**Anchor / Jangkar:** P2 (one status model across queue, Overview, Report), P4.
**Classification:** INTERNAL
**Artefacts:** repo `queue.html`, `dashboard.html`, `base.html`, `main.py`, `audit/log.py` (`latest_notes()`), `app.css`, `steps.js`, `README.md`; BUILD-LOG 19:05, 19:15, 19:20, 19:35, 20:50. `/network` now redirects to Overview; `network.html` unused.
**Verification / Verifikasi:**
  - Live with the new queue and Overview — VERIFIED-AGAINST-SoR (owner screenshots 19:18 and 19:23 of live; `/health` 0.16.2-judges 23:05)
  - Search bug on live found and fixed — RECONCILED (live 0.15.2 reproduced in Chrome 19:10: rows hidden by attribute but shown by CSS; fixed 0.15.3; lesson in BUILD-LOG)
**Open items / Item terbuka:** none.
**Next / Lanjutan:** none; freeze.

## D-2026-10-15-32 — Repo public; keep docs/governance public (owner, HS3)

**Decision / Keputusan:** [EN] Switch the GitHub repo to Public on Thu 20:00 after a clean secret scan; keep `docs/governance/` in the public repo. / [ID] Repo dibuat Public Kam 20:00 setelah secret scan bersih; `docs/governance/` tetap ikut publik.
**Trigger / Pemicu:** Owner 19:50 "link github dibuka saja"; AskUserQuestion 19:52 "Keep it".
**Framework / Kerangka:** PI §3.4 HS3 (irreversible: owner only); Jira UBP-19 → UBP-20.
**Anchor / Jangkar:** P1 (decision trail public), P5, P7.
**Classification:** PUBLIC (repo)
**Artefacts:** BUILD-LOG 19:55; Jira UBP-19 comment 12453, UBP-20 comment 12454 (both Done).
**Verification / Verifikasi:**
  - Secret scan clean — VERIFIED-AGAINST-SoR (agent scan of 67 working-tree files; owner `git log --all -p` filter, empty output)
  - Repo is Public — VERIFIED-AGAINST-SoR (owner screenshot of the repo README 20:00); logged-out check by owner — ASSUMED → verify-by: SoR=open the repo in incognito; agent=A4-PER-THX-01; by=Fri 11:00
**Open items / Item terbuka:** none.

## D-2026-10-16-01 — Session lock Thu evening (owner)

**Decision / Keputusan:** [EN] Lock: live v0.16.2-judges; Devpost draft filled (story, tags, links, 11 screenshots with captions); pitch deck (13 slides) and 5-minute video script ready; Jira updated. No new features before submit. Freeze Fri 09:00 and submit Fri 11:30 unchanged. / [ID] Lock sesi Kamis malam; tidak ada fitur baru sebelum submit; freeze dan submit tidak bergeser.
**Trigger / Pemicu:** Owner 00:44 "lock, update jira dan hand off".
**Framework / Kerangka:** PI §3.5 checkpoints.
**Anchor / Jangkar:** P4, P6.
**Classification:** INTERNAL
**Artefacts:** this shard; `HANDOFF_Fri_Session5_2026-10-16.md`; LOCK-REGISTER rows D-29…D-32, D-2026-10-16-01; index changelog; Claude Slides "UltraByte pitch (OLG + Main Track)"; Claude Doc "UltraByte Demo Video Script (5 min)"; repo `demo/gallery/` (11 PNG), `devpost_story.md` (chat file); thumbnail PNG in repo brand folder.
**Verification / Verifikasi:**
  - Live version — VERIFIED-AGAINST-SoR (`/health` 0.16.2-judges 23:05)
  - Jira — VERIFIED-AGAINST-SoR (UBP-19, UBP-20, UBP-30 → Done; comments on UBP-16, 17, 18, 24; 00:45)
  - Devpost draft saved — ASSUMED → verify-by: SoR=Devpost project page shows story + gallery after reload; agent=A4-PER-THX-01; by=Fri 09:00
  - Repo HEAD contains v0.16.2 + BUILD-LOG rows — ASSUMED (owner commits) → verify-by: SoR=`git log -1` + `git status` clean; agent=A4-PER-THX-01; by=Fri 09:00
**Open items / Item terbuka:** see handoff §5.
**Next / Lanjutan:** handoff §4.
