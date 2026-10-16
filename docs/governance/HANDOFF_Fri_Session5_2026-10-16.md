# HANDOFF — Sesi 5: Jumat pagi → freeze → submit → pitch

**Dari:** A4-PER-THX-01 sesi 4 (Kam 18:53 → Jum 00:45 EDT) · **Ke:** sesi Jumat pagi (owner + Claude) · **Ditulis:** 2026-10-16 00:45
**Acuan:** PI §3.5 · K0 v0.7 · repo `BUILD-LOG.md` rows 19:05 → 23:00 · shard PART4 (D-29…D-32, D-2026-10-16-01) · LOCK-REGISTER · Jira UBP
**Menggantikan:** `HANDOFF_Thu_Session4_2026-10-15.md`
**Mode:** tidak ada fitur baru. Hanya bugfix, rekam video, Devpost, submit.

## 1. Posisi saat handoff

| Item | Status |
|---|---|
| Live | https://ultrabyte.denysetya.com, **v0.16.2-judges**, `/health` ok 23:05 (VERIFIED). Demo accounts tampil di `/login` (VERIFIED). |
| Repo | Public sejak Kam 20:00 (owner). HEAD berisi s/d 0.16.2 = ASSUMED (owner `git log -1`). |
| VPS | `.env` + `DEMO_LOGINS`; container dibuat ulang via `docker compose -p ultrabyte-app up -d --force-recreate`. Selalu pakai `-p ultrabyte-app` atau `/opt/ultrabyte/deploy.sh`. |
| Devpost | Submission 1237964 DRAFT: nama, pitch, story, 15 tag, 3 link, 11 gambar + caption. Save = ASSUMED. Video dan Submit belum. |
| Deck | Claude Slides "UltraByte pitch (OLG + Main Track)", 13 slide, notes + timing, export PPTX/PDF. Privat. |
| Video script | Claude Doc "UltraByte Demo Video Script (5 min)", 10 adegan. Privat. |
| Jira | UBP-19, 20, 30 Done; komentar di 16, 17, 18, 24. |

## 2. Yang berubah di sesi 4 (detail di BUILD-LOG)

Review queue jadi inbox investigator (With comment, To do, Escalated & monitor, Dismissed; angka to-do di menu). Kasus yang direspons compliance pindah ke Overview (In progress, Resolved). Overview: tombol "?", search, kartu sama besar, Shared cards masuk Overview. Menu Daily work / Manage; Validation jadi tombol "Version 1.0 vs 2.0". Report + CSV (D-29). Akun demo di login (D-30). Fix: search tidak menyembunyikan baris; "&" ter-escape dua kali. Secret scan bersih, repo Public (D-32).

## 3. Verify-by di awal sesi (5 menit)

1. `git log -1` dan `git status` bersih; `/health` = 0.16.2-judges.
2. Incognito: repo GitHub terbuka; `/login` → klik **investigator** → Sign in → Review queue tampil.
3. Buka `/report` (masuk sebagai compliance): jumlah kartu = jumlah baris tabel.
4. Devpost: reload halaman edit, cek story, tag, link, gambar, caption masih ada.

## 4. Urutan kerja sampai pitch

| Waktu (EDT) | Apa | Siapa |
|---|---|---|
| ≤ 09:00 | **Freeze**: `git tag v1.0-demo && git push --tags`; Reset demo data; Reset count (V1 dan V2); rekam video pakai script (≤ 5:00) | Owner |
| ≤ 10:00 | Upload video (YouTube unlisted atau Devpost); tambah 1 kalimat "demo accounts on the login page" di story | Owner |
| ≤ 10:30 | Isi nama tim di deck; cek angka slide 7 dengan `/validation` live; share deck ke tim | Owner + tim |
| ≤ 11:30 | **Submit Devpost** (HS3): tick OLG + Main Track, cek semua isian | Owner |
| 12:15 | Score rules = default; Reset demo data; Reset count | Owner |
| 12:30–14:30 | Presentasi; video cadangan siap di laptop | Tim |
| Setelah judging | Hapus `DEMO_LOGINS` dari `.env` + `deploy.sh`; UBP-26 retro, UBP-27 teardown (≤ 23 Okt) | Owner |

## 5. Open items (owner-gated)

- Folder lokal owner-of-record A4-PER-THX-01 masih belum tersambung ke sesi; shard PART2, PART3, PART4, LOCK-REGISTER, index, handoff menunggu salin dari repo `docs/governance/` atau Project docs.
- Baris BUILD-LOG hasil secret scan sempat hilang di laptop (kemungkinan tertimpa operasi git) dan sudah ditambahkan ulang 20:50; cek tidak ada baris lain yang hilang (`git diff` terhadap commit sebelumnya).
- Demo accounts publik: siapa pun bisa login compliance dan mengubah rules atau reset data. Mitigasi: reset sebelum pitch.
- Lama: V1 layar 3–6 ASSUMED (UBP-22); rujukan primer harm SG (lane d); tautan V2 → `/v1`.
- Master-Index writeback (`agh-index-writeback`) setelah event.

## 6. Q&A tambahan

- "Can anyone log in?" → Yes, demo accounts for judges on synthetic data; removed after judging.
- "Where is the report data from?" → Only the append-only audit trail and the scores; nothing is stored separately.
- "Why does a case disappear from the queue?" → Once compliance picks it up, it is compliance's work; the investigator queue stays short, and Overview and Report keep the full picture.
