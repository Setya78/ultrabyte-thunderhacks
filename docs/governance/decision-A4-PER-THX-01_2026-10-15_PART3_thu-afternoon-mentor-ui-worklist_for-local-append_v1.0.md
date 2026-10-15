# decision-A4-PER-THX-01 — SHARD PART3 (2026-10-15, Thu afternoon 13:00–18:00 EDT) — for local append

> Mirror for preflight discoverability. Not authoritative. Owner of record: `04_decision_log/decision-A4-PER-THX-01.md` (local master, not reachable from this session). Append after PART2. Sprint-level rows live in repo `BUILD-LOG.md` (PI §3.6); this shard records only project-level locks and the session lock.

---

## D-2026-10-15-25 — Bobot cek tetap 4 × 25 / Check weights stay 4 × 25

**Decision / Keputusan:** [ID] Empat cek AML tetap berbobot sama (25 poin) sampai ada data outcome nyata; sinyal paling serius (red flag FINTRAC, account takeover) sudah mendahului skor lewat label. Tidak melatih model pada data sintetis. / [EN] The four AML checks keep equal weights (25 each) until calibrated on real outcomes; the most serious signals already override the score through labels. No model is trained on the synthetic data.
**Trigger / Pemicu:** Masukan mentor OLG (Dhruv Kalra, DM 14:43–14:53) "weight some factors more, maybe train a model"; owner 15:03 "tetap 4 × 25".
**Framework / Kerangka:** P5 (uncertainty): bobot tanpa data outcome = angka karangan yang tampak seperti insight; P7 (misuse): model dari data sintetis hanya mempelajari aturan yang ditanam.
**Anchor / Jangkar:** L2-02 P5, P7; K0 v0.7 §3 (4 × 25); IN-07 §5.
**Classification:** INTERNAL.
**Artefacts:** README "Known simplifications" (equal weights); pitch/Q&A line; BUILD-LOG D-25; Jira UBP-22 comment 12451.
**Verification / Verifikasi:**
  - README line live — VERIFIED-AGAINST-SoR (repo README in v0.14.0-mentor deploy; `/health` 0.14.0 at 16:33).
**Open items / Item terbuka:** none.
**Next / Lanjutan:** Q&A fallback in Demo Guide §Recording rules.

---

## D-2026-10-15-26 — HS4: hand-off kasus antar peran / Case hand-off between roles

**Decision / Keputusan:** [ID] Dibangun sekarang, minimal: investigator escalate → compliance "Mark as handling" (In progress) → "Mark resolved"; dua aksi audit append-only baru (`handling`, `resolve`, migrasi 006); status kasus = baris terakhir per pemain; kedua peran melihat status yang sama; tabel Decided di Review queue dikelompokkan per status. Agent merekomendasikan menunda (freeze 15 jam lagi); owner memilih bangun. / [EN] Build now, minimal: investigator escalates, compliance marks In progress then Resolved; two new append-only audit actions (migration 006); case status = latest row per player; both roles see the same status. Agent recommended deferring; owner chose to build.
**Trigger / Pemicu:** Owner 17:32 "harusnya ada mark resolve dan mark sedang dihandle jadi antara compliance dan investigator saling tahu posisinya".
**Framework / Kerangka:** PI §3.4 HS4 (fitur baru di luar K0 yang mengubah demo story) → dua opsi diajukan, owner memutuskan A. P4 (accountability: setiap langkah bernama dan berwaktu), P6 (append-only).
**Anchor / Jangkar:** L2-02 P4, P6; PI §3.4; D-2026-10-14-11 (migrasi bergate); D-2026-10-15-20 (dua peran).
**Classification:** INTERNAL.
**Artefacts:** repo `db/migrations/006_case_status.sql`, `app/audit/log.py` (STATUS_ACTIONS, STATES, case_status), `app/main.py` (`POST /player/{pid}/status`, compliance only), `queue.html`, `player.html`, `app.css`; README (Case hand-off row + Deploy note); BUILD-LOG D-26 + 17:55 row.
**Verification / Verifikasi:**
  - Code live in v0.15.0-worklist — VERIFIED-AGAINST-SoR (`/health` version 0.15.0-worklist 18:00; `app.css` served with "Case status chips" block).
  - Migration 006 applied on VPS — ASSUMED → verify-by: SoR=`pg_get_constraintdef` of `audit_event_action_check` must list handling/resolve; agent=owner (A4-PER-THX-01 records); by=before recording the video (Thu 21:30).
  - Hand-off flow works end to end (escalate → handling → resolve, 403 for investigator) — ASSUMED → verify-by: SoR=live smoke by owner on P-8104 with both accounts; agent=owner; by=Thu 21:30.
**Open items / Item terbuka:** Demo Guide scene 8 may open with the 10-second hand-off (owner to confirm).
**Next / Lanjutan:** owner smoke; if it fails, the fallback is to leave the buttons unused in the video (status chips still render).

---

## D-2026-10-15-27 — Session lock Kamis sore: v0.15.0-worklist live, mentor input applied, UI theme, worklist, Demo Guide

**Decision / Keputusan:** [ID] Owner mengunci sesi 13:00–18:00 EDT. Live = v0.15.0-worklist (+ hotfix `priority`). Isi: (1) jawaban ALCOMS 15:07 "Version 1.0 boleh proses generik asalkan dijelaskan dan ditunjukkan perbaikannya" → kelayakan `/v1` untuk Main Track: ASSUMED → confirmed by organizer (informal, chat); (2) masukan mentor OLG Dhruv Kalra (informal, bukan kebijakan OLG) diterapkan: tabel Expected vs actual di player page, saran URGENT "step-up verification (2FA/email)", README (income where available, bobot sama, mentor = informal); (3) lokasi Ontario: ASSUMED → sourced AGCO Registrar's Standards for Internet Gaming Standard 3.02 (pandangan mentor berbeda, dicatat informal); app tidak pernah memblokir pemain, lokasi = sinyal takeover; (4) tema UI "Sapphire sidebar" (opsi A dari 3 render), teks gelap, tombol aksi terlihat, popover "?" tidak terpotong, lingkaran skor berwarna band (merah/kuning/hijau); (5) Manual entry: ID otomatis (pilihan New/Existing), nama depan + belakang fiktif disimpan "First L.", pekerjaan dari daftar seed per income band (melonggarkan D-16 "names generated, never typed", mitigasi dicatat); (6) Review queue = worklist: Action required vs Decided, search nama/ID, chip filter band + kategori, tag NEW (manual/import), Overview grup "Newly added"; (7) hand-off kasus (D-26); (8) nginx `client_max_body_size 20m` di VPS untuk Import; (9) Demo Guide (Claude Doc) berisi manual investigator/compliance, kasus, skrip video 5 menit v2 (9 adegan, manual entry + Excel), tabel kebutuhan juri Main vs OLG, aturan rekaman; (10) skill `laptop-repo-change-loop` dibuat (stage → edit → verify → write back → log → commit message → verify live). / [EN] Owner locks the Thursday-afternoon session: v0.15.0-worklist live; organizer confirmation for the generic V1; OLG mentor input applied and labelled informal; Ontario location sourced to AGCO 3.02; new UI theme and readability; dataset-aligned manual entry; worklist split with search/filters; case hand-off; nginx upload limit; Demo Guide doc; change-loop skill.
**Trigger / Pemicu:** Owner 18:00 "lock dulu /decision-log-writer".
**Framework / Kerangka:** PI §3 continuous build (wording/UI tanpa gate; HS4 dua kali: bobot → tetap, hand-off → bangun); P1 (sumber: ALCOMS chat 15:07, DM mentor, AGCO 3.02 fetched); P5 (ASSUMED/confirmed/sourced dipisah); P7 (tidak ada klaim performa selain uji logika).
**Anchor / Jangkar:** L2-02 P1, P4, P5, P6, P7; PI §3.4–3.6; D-16, D-19, D-20, D-22, D-24.
**Classification:** INTERNAL (chat mentor/organizer = screenshot owner, tidak di repo).
**Artefacts:** repo (owner commits): `app/main.py`, `app/judge.py`, `app/importer.py`, `app/audit/log.py`, `app/scoring/engine.py`, `app/static/app.css`, `app/templates/{base,login,v1_base,player,queue,enter,_ring}.html`, `db/migrations/006_case_status.sql`, `README.md`, `BUILD-LOG.md` (rows 15:11 → 17:55, D-25, D-26); Claude Doc "UltraByte Demo Guide" (artifact a1ea67a8-ae34-4f7a-a9e9-e7e950d52210, private until shared); Jira UBP-22 comments 12451, 12452; skill `laptop-repo-change-loop` (user skills); nginx server block on VPS (not in repo; README Deploy note); this shard PART3; LOCK-REGISTER rows D-25, D-26, D-27; index rows.
**Verification / Verifikasi:**
  - Live version 0.15.0-worklist, DB ok, 501 players — VERIFIED-AGAINST-SoR (`/health` 18:00 EDT).
  - Served `app.css` carries theme A, darker text, popover fix, rings-by-band, queue chips, status chips — VERIFIED-AGAINST-SoR (curl markers 18:00).
  - Review queue renders after sign-in (post-hotfix) — ASSUMED → verify-by: SoR=owner opens `/` signed in; agent=owner; by=Thu 18:30.
  - Repo HEAD hash for v0.15.0 + hotfix — ASSUMED (owner committed; hash not read) → verify-by: SoR=`git log -1` on laptop; agent=owner; by=next session (handoff).
  - Migration 006 on VPS; hand-off flow — ASSUMED (see D-26).
  - Excel import succeeds after nginx change — ASSUMED → verify-by: SoR=owner Import (Add) of repo workbook; agent=owner; by=Thu 21:30.
  - Project-files copy of `UltraByte_demo_300_players.xlsx` replaced (D-24 ASSUMED) — STALE: agent checked the Project-files copy 15:13 = old (210 distinct names) while repo copy = 308/308 → verify-by: SoR=re-upload in Project files; agent=owner; by=Fri 09:00. Index row DEMO-XLSX notes updated; Master-Index writeback flagged.
  - V1 routine screens 3–6 realistic — ASSUMED (follow-up Q to mentor unanswered) → verify-by: SoR=mentor reply or none; agent=A4-PER-THX-01; by=Fri 09:00 (then stays ASSUMED and labelled in README/deck).
**Open items / Item terbuka:** owner smoke of hand-off; migration 006 on VPS; Demo Guide share with team (private now); scene 8 wording; Project-files workbook replace; LOCK-REGISTER local master append (PART2 + PART3); freeze Fri 09:00 — no feature after this lock (agent recommendation; owner authority).
**Next / Lanjutan:** owner: rebuild/smoke done → record video from Demo Guide; agent next session: live check of hand-off, README final, Devpost final (UBP-17), tag `v1.0-demo` at freeze, secret scan, repo public (HS3).

---

## D-2026-10-15-28 — Lock 18:42: hand-off box untuk compliance di semua player page, filter dropdown + status, chip status di nama; evaluasi di sesi baru

**Decision / Keputusan:** [ID] Owner mengunci tambahan setelah D-27 dan menunda evaluasi ke sesi baru: (1) kotak hand-off (Mark as handling / Mark resolved) tampil untuk compliance di setiap player page tanpa perlu Escalate dulu; investigator hanya melihat baris status; (2) filter Review queue menjadi tiga dropdown (Band, Category, Status: Action required / Escalated / In progress / Monitor / Dismissed / Resolved) + Clear, menggantikan baris chip; (3) chip status di samping nama pemain di tabel Decided dan di Overview (plus tag NEW di Overview); (4) migrasi 006 diterapkan di VPS 18:07 (perlu `bash scripts/migrate.sh`, bit eksekusi hilang dari checkout Windows), README Deploy diperbarui; (5) tidak ada fitur baru lagi; sesi berikut = evaluasi + README/Devpost final + rekaman. / [EN] Owner locks the post-D-27 additions and defers evaluation to a new session: compliance hand-off box on every player page; dropdown filters incl. case status; status chip beside the name on queue and Overview; migration 006 applied on the VPS; no further features.
**Trigger / Pemicu:** Owner 18:16, 18:20 (dua pesan), 18:42 "ok lock dulu dan kita evaluasi lagi di sesi baru".
**Framework / Kerangka:** PI §3 (wording/UI tanpa gate; D-26 sudah HS4); P4 (status bernama dan berwaktu di setiap tampilan); P6 (append-only, Reset mengosongkan status).
**Anchor / Jangkar:** L2-02 P4, P6; D-26, D-27.
**Classification:** INTERNAL.
**Artefacts:** repo `app/templates/{player,queue,dashboard}.html`, `app/main.py` (dashboard membaca `case_status`), `app/static/app.css`, `README.md` (Deploy: `bash scripts/migrate.sh`), `BUILD-LOG.md` rows 18:20, 18:30; shard ini (PART3 addendum); LOCK-REGISTER row D-28; index changelog.
**Verification / Verifikasi:**
  - Live `app.css` carries "Queue filters as dropdowns" block; `/health` 0.15.0-worklist, audit_events 1 (owner reset) — VERIFIED-AGAINST-SoR (curl 18:43).
  - Migration 006 on VPS — RECONCILED (was ASSUMED in D-26; owner psql output 18:07 lists handling/resolve).
  - Hand-off end to end — RECONCILED (was ASSUMED; owner screenshot 18:19: P-4501 "In progress, compliance").
  - Hand-off box on every player page + status chips live — ASSUMED → verify-by: SoR=owner opens P-4501 as compliance without a prior Escalate and sees the box; Overview shows the chip; agent=owner; by=next session start.
  - Repo HEAD hash — ASSUMED → verify-by: SoR=`git log -1`; agent=owner; by=next session (write into handoff).
  - VERSION not bumped for the 18:20–18:30 CSS change (still 0.15.0-worklist) — known; browsers may need Ctrl+F5 once → verify-by: bump to 0.15.1 at the next deploy; agent=A4-PER-THX-01; by=next session.
**Open items / Item terbuka:** evaluasi sesi baru (apa yang dipotong untuk video 5 menit); Demo Guide adegan 8 (hand-off 10 detik) belum ditulis; Demo Guide belum di-share ke tim; README/Devpost final (UBP-16/17); salinan Project-files workbook STALE; V1 layar 3–6 ASSUMED; freeze Jum 09:00.
**Next / Lanjutan:** sesi baru dimulai dengan: `/health`, `git log -1`, bump 0.15.1 bila ada CSS, lalu evaluasi dari Demo Guide; tidak ada fitur baru (D-27, D-28).
