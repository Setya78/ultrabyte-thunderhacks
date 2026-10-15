# HANDOFF — Sesi 4: evaluasi Kamis malam / Jumat pagi → freeze → submit

**Dari:** A4-PER-THX-01 sesi 3 (13:00–18:45 EDT, Kam 15 Okt) · **Ke:** sesi evaluasi (owner + Claude) · **Ditulis:** 18:45 EDT
**Acuan:** PI §3 · K0 v0.7 · repo `BUILD-LOG.md` (rows 15:11 → 18:30, D-25, D-26) · shard PART3 (D-25…D-28) · LOCK-REGISTER · Demo Guide (Claude Doc) · Jira UBP-22 comments 12451/12452.
**Menggantikan:** `HANDOFF_Thu_Session3_2026-10-15.md` (demo script §4 digantikan Demo Guide skrip v2).
**Mode:** D-27/D-28: **tidak ada fitur baru**. Hanya bugfix, README, Devpost, deck, video. Freeze Jum 09:00 tidak bergeser.

## 1. Posisi saat handoff

| Item | Status |
|---|---|
| Live | https://ultrabyte.denysetya.com — **v0.15.0-worklist**, `/health` ok 18:43, audit trail di-reset (1 event). CSS terbaru (dropdown filter) tersaji |
| HEAD | ASSUMED: commit terakhir owner ~18:40 memuat queue/dashboard/main/app.css/BUILD-LOG. Hash belum dibaca → `git log -1` di awal sesi |
| Belum di-commit | kemungkinan `docs/governance/` (3 file mirror PART3) + file sesi ini bila owner belum commit; cek GitHub Desktop |
| DB VPS | migrasi 001–006 applied (006 VERIFIED 18:07 via psql) |
| nginx | `client_max_body_size 20m` di kedua server block (16:55) |
| Validasi | tidak berubah oleh sesi ini: 9/9, 0/2, 6/490, 15/15; kasus H 7 vs 2 langkah |
| Demo Guide | Claude Doc (privat). Skrip v2 9 adegan; adegan 8 belum memuat hand-off 10 detik |
| Jira | UBP-22 comments (mentor, organizer, AGCO). UBP-16/17 (README/Devpost final) belum |

## 2. Yang berubah di sesi 3 (ringkas; detail BUILD-LOG)

Mentor OLG (informal): Expected vs actual table, step-up wording, README notes; bobot tetap 4 × 25 (D-25). ALCOMS: V1 generik OK. Lokasi Ontario → AGCO 3.02. Tema Sapphire + teks gelap + tombol + popover + lingkaran per band. Manual entry selaras dataset (New/Existing, First + Last fiktif → "First L.", pekerjaan dari daftar seed). Review queue = worklist (Action required vs Decided), search, dropdown filter Band/Category/Status, tag NEW, Overview "Newly added". Hand-off kasus (D-26, migrasi 006): compliance Mark as handling / Mark resolved di setiap player page; chip status di nama. Hotfix `priority`. Skill `laptop-repo-change-loop`.

## 3. Verify-by di awal sesi (5 menit)

1. `/health` = 0.15.0-worklist; `git log -1` → tulis hash ke BUILD-LOG.
2. Login compliance → buka P-4501 **tanpa** Escalate → kotak hand-off tampil; Overview menunjukkan chip status. (D-28 ASSUMED → VERIFIED)
3. Bump VERSION ke `0.15.1` pada deploy berikutnya (CSS berubah 18:20–18:30 tanpa bump).
4. Ganti `UltraByte_demo_300_players.xlsx` di Project files dengan versi repo (STALE sejak 15:13).
5. Share Demo Guide ke tim (masih privat).

## 4. Urutan kerja sampai submit

| Waktu (EDT) | Apa | Siapa |
|---|---|---|
| Sesi evaluasi | Jalankan skrip Demo Guide sekali penuh; putuskan apa yang dipotong untuk 5 menit; tulis adegan 8 hand-off (10 dtk) | Owner + Claude |
| Kam malam | README final (UBP-16): arsitektur 1 diagram, how to run, migrasi 006 + nginx, AI disclosure, mentor = informal, AGCO 3.02; Devpost final (UBP-17): 7 → 2 langkah, 1/9 → 9/9, hand-off | Claude |
| Kam malam | Deck pitch 9 slide dari deck V1 vs V2 + slide hand-off; Q&A: bobot sama, V1 = reconstruction, geofence, "9 of 9 on designed cases" | Tim |
| Jum ≤09:00 | **Freeze**: tag `v1.0-demo`; Reset demo data; Reset count; rekam video | Owner |
| Jum ≤10:30 | Secret scan repo (`.env` tidak ikut; password tidak di README/BUILD-LOG) | Claude |
| Jum ≤11:00 | Repo → Public (HS3 owner) | Owner |
| Jum ≤11:30 | Submit Devpost (HS3 owner) | Owner |
| Jum 12:30–14:30 | Presentasi & judging | Tim |

## 5. Open items (owner-gated)

- V1 layar 3–6 tetap ASSUMED (mentor belum balas); label "reconstruction" di app, README, deck.
- Referensi primer 4 penanda Safer Gambling (lane d) masih ASSUMED di README.
- Tautan V2 → `/v1` (Gina 2×): belum; D-22 tetap.
- Folder project lokal owner-of-record belum tersambung sejak D-15; shard PART2 + PART3, LOCK-REGISTER, index menunggu append/salin (mirror ada di repo `docs/governance/`).
- Master-Index writeback wajib (klaim STALE workbook) → `agh-index-writeback` setelah event.

## 6. Q&A siap pakai (tambahan sesi 3)

- "Why equal weights?" → No real outcomes yet; serious signals (FINTRAC red flags, takeover) already override the score through labels; compliance can change thresholds today.
- "Do you block players outside Ontario?" → No. AGCO 3.02 requires play within Ontario; we only flag impossible travel as a takeover signal and ask for step-up verification.
- "Did OLG validate this?" → An OLG mentor gave informal design feedback during the event; nothing here is OLG policy.
- "Who closes a case?" → Investigators decide; compliance picks escalated cases up and resolves them; every step is an append-only audit row with name and time.
