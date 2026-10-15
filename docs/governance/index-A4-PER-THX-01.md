# INDEX — ThunderHacks II Build Sprint

**Stable Tag:** A4-PER-THX-01
**Index Version:** v1.1
**Workflow Standard:** L3-01 §4 / §4.6 (per-agent filenames) — version label OPEN, lihat §8
**Effective Date:** 2026-10-10 · **Sunset:** 2026-10-23
**Steward:** Owner (Jojo Setiawan)
**Language:** Bilingual — diskusi ID; code, README, pitch, commit EN (PI §5)
**Classification:** INTERNAL (repo publik saat submit Jum 16 Okt ≤11:30, HS3 owner)

---

## 1. Purpose

Single navigation entry-point untuk folder A4-PER-THX-01. Semua artefak project harus dapat ditemukan dari index ini. Repo code hackathon berada **di luar** folder ini (§7).

## 2. Folder Structure

| Folder | Purpose | Examples |
|---|---|---|
| `00_baselines/` | Locked, read-only | PI v1.0, BL-MVP-01, K0 |
| `01_artefacts/` | Final deliverable | LOCK-REGISTER, logo mark, workbook demo, deck V1 vs V2, retro 1 halaman |
| `02_working/` | Draft | Handoff, Devpost draft, demo script |
| `03_inputs/` | Raw input, nama asli | Spawn package, brief, transkrip, IN-07, logo tim, review Gina |
| `04_decision_log/` | Keputusan level project | `decision-A4-PER-THX-01.md` + shard PART2, PART3 2026-10-15 |
| `05_index/` | Manifest ini | `index-A4-PER-THX-01.md` |

## 3. Baselines (00_baselines/)

| Doc ID | Title | Version | Status | Date | Notes |
|---|---|---|---|---|---|
| PI-THX-01 | `PI_A4-PER-THX-01_v1.0.md` — Project Instructions | v1.0 | LOCKED | 2026-10-10 | D-2026-10-10-04 |
| BL-MVP-01 | `THX_MVP_Build_Baseline_v1.0.md` — MVP Build Baseline | v1.0 | LOCKED | 2026-10-14 | D-2026-10-14-01/-02; §7 logo SUPERSEDED by D-14 (logo tim); mirror Confluence 104562689 |
| K0 | `K0_Kickoff_Lock_A4-PER-THX-01.md` — Kickoff Lock | v0.7 | LOCKED | 2026-10-14 19:12 | D-2026-10-14-07 (supersedes v0.6 D-06); amandemen scope via HS4 D-16, D-19, D-20, D-22 (§3 M2 toggle dan §5 langkah 1 superseded oleh D-22); dicatat di decision log, K0 tidak di-bump |

## 4. Artefacts (01_artefacts/)

| Artefact ID | Title | Date | Status | Notes |
|---|---|---|---|---|
| LOCK-REGISTER | `LOCK-REGISTER_A4-PER-THX-01.md` | 2026-10-15 | ACTIVE (mirror) | AMEND 18:05: + D-25, D-26, D-27; notes D-07, D-11, D-15, D-16, D-20, D-22, Overview-groups |
| LOGO-MARK | `THX_logo-mark-U_2026-10-14.png` — mark "U" dari logo tim (512 px) | 2026-10-14 | FINAL | D-14; AI-generated (Gemini), disclosed di README repo |
| LOGO-DRAFT | `THX_logo-v1_2026-10-14.svg`, `THX_logo-v2_2026-10-14.svg` — draft "Eight Bits" | 2026-10-14 | SUPERSEDED | Project docs only; tidak dipakai |
| DEMO-XLSX | `UltraByte_demo_300_players.xlsx` — 308 pemain sintetis, skenario tertanam | 2026-10-15 | FINAL (mirror) | AMEND D-24: owner of record = repo `demo/` (308/308 nama unik, VERIFIED 15:22 dari salinan repo). Salinan Project files = **STALE** (dicek 15:13: 210 nama unik, 77 duplikat) → owner ganti sebelum Jum 09:00 (D-27 verify-by) |
| DECK-V1V2 | `UltraByte_V1_vs_V2_explainer_draft.pptx` — 11 slide, speaker notes | 2026-10-15 | DRAFT (review tim) | D-24; NEW; Main 4 syarat, V1 rutinitas, 7 vs 2 langkah, rubrik OLG, migrasi, batasan; input UBP-24 |
| DEMO-GUIDE | "UltraByte Demo Guide" — Claude Doc (artifact `a1ea67a8-ae34-4f7a-a9e9-e7e950d52210`): manual investigator & compliance, kasus, skrip video 5 menit v2 (9 adegan), kebutuhan juri Main vs OLG, aturan rekaman | 2026-10-15 | ACTIVE (owner of record = Claude Doc; privat sampai di-share) | D-27; NEW; location = Claude Docs (bukan folder); export .docx/PDF tersedia; adegan 8 hand-off belum ditambahkan (owner) |
| SKILL-LOOP | `laptop-repo-change-loop` — user skill: stage → edit → verify → write back → BUILD-LOG → commit message → verify live | 2026-10-15 | ACTIVE | D-27; NEW; location = user skills (bukan folder project); pelajaran 17:55: tes render wajib memakai objek engine asli |

## 5. Working Drafts (02_working/)

| Draft ID | Linked Artefact / Input | Stage | Last Updated | Notes |
|---|---|---|---|---|
| WD-01 | `HANDOFF_M0_Build_2026-10-14.md` → sesi build M0 | DONE (dieksekusi) | 2026-10-14 19:12 | D-07 rev |
| WD-02 | `DEVPOST_Draft_2026-10-14.md` → UBP-17 | draft | 2026-10-14 20:35 | Belum memuat sign-in, Rules, SG, AI summary, About, `/v1`; final sesi berikutnya |
| WD-03 | `HANDOFF_Thu_Feedback_2026-10-14.md` → sesi Kamis | SUPERSEDED | 2026-10-15 08:15 | digantikan WD-04 |
| WD-04 | `HANDOFF_Thu_Session2_2026-10-15.md` → sesi 2 Kamis | SUPERSEDED | 2026-10-15 08:55 | D-21; digantikan WD-05 (demo script §5 langkah 2 tidak berlaku lagi) |
| WD-06 | `HANDOFF_Thu_Session4_2026-10-15.md` → sesi evaluasi (Kam malam / Jum pagi) | handoff | 2026-10-15 18:45 | D-28; posisi live, verify-by list, urutan kerja sampai submit |
| WD-05 | `HANDOFF_Thu_Session3_2026-10-15.md` → sesi 3 Kamis | SUPERSEDED | 2026-10-15 10:15 | D-24; demo script §4 SUPERSEDED oleh Demo Guide skrip v2 (D-27); README/Devpost final belum |

## 6. Inputs (03_inputs/)

| Input ID | Source | Type | Date Received | Notes |
|---|---|---|---|---|
| IN-01 | `A4-PER-THX-01_Spawn_Package_2026-10-10.md` | Spawn package | 2026-10-10 | Verbatim |
| IN-02 | `D-2026-10-10-04_seed_for_A4-PER-CAR-01.md` | Decision seed | 2026-10-10 | Untuk log hub |
| IN-03 | `IN-03_Opening_Audio_Transcripts_2026-10-14.md` | Transkrip opening | 2026-10-14 16:32 | Belum diverifikasi kata per kata |
| IN-03h | `Workshop_Money_laundring_-_Transcript.pdf` | Transkrip workshop AML | 2026-10-14 17:09 | — |
| IN-04 | thunderhacks-ii.devpost.com + /rules | Web | 2026-10-14 16:44 | AI tools ALLOWED + disclose; multi-track OK |
| IN-05 | `ThunderHacksII_Main_Track_Problem_Statement_Version_2.0.pdf` | Brief Main | 2026-10-14 17:17 | Dibaca ulang 2026-10-15 08:55 (D-22) |
| IN-06 | `ThunderHacksII_OLG_Problem_Statement_CONFIDENTIAL.pdf` | Brief OLG | 2026-10-14 17:18 | ⚑ Confidential: tidak masuk repo |
| IN-07 | `IN-07_Team_Challenge_Analysis_2026-10-14.md` | Dokumen tim (.docx → md) | 2026-10-14 19:09 | Mengutip brief OLG: internal; D-07 |
| IN-08 | `Gemini_Generated_Image_gqakbkgqakbkgqak.jpeg` | Logo tim (AI-generated) | 2026-10-14 21:24 | D-14; disclosed |
| IN-09 | Feedback owner 15 Okt 07:50–08:43 (chat + screenshot) | Feedback round 1 | 2026-10-15 | Dicatat di BUILD-LOG 07:55–08:50; tidak disimpan sebagai file |
| IN-10 | `UltraByte_-_App_Review_Feedback_for_Jojo.docx` (Gina) | Review app v0.11 | 2026-10-15 09:38 | Diterima di chat; 13 item → BUILD-LOG 10:05; file belum di folder lokal (owner) |
| IN-11 | `UltraByte_-_App_Review_Feedback_for_Jojo_1.docx` (Gina) + WhatsApp tim (Evi, Gina) | Review v0.12–0.13 + `/v1` + HP | 2026-10-15 10:04 | V1–V4 → BUILD-LOG 10:20; ringkasan di Jira UBP-28 |
| IN-12 | Dhruv Kalra (OLG mentor), WhatsApp DM 14:43–14:53 + 16:05 | Masukan mentor (informal, bukan kebijakan OLG) | 2026-10-15 | Screenshot owner; dicatat Jira UBP-22 comment 12451, 12452; BUILD-LOG 15:11, 16:15; tidak disimpan sebagai file |
| IN-13 | ALCOMS organizer, WhatsApp Questions group 15:07 | Konfirmasi Main Track: V1 boleh proses generik bila dijelaskan + perbaikan ditunjukkan | 2026-10-15 | Screenshot owner; UBP-22 comment 12451 |
| IN-14 | AGCO Registrar's Standards for Internet Gaming, Standard 3.02 (agco.ca, fetched 16:05) | Sumber primer lokasi Ontario | 2026-10-15 | README Known simplifications; UBP-22 comment 12452 |

## 7. Decision Log & External Pointers

- Decision log project: `04_decision_log/decision-A4-PER-THX-01.md` (D-04…D-07, D-15, D-16, D-19, D-20, D-21) + shard PART2 (D-22, D-24) + shard `decision-A4-PER-THX-01_2026-10-15_PART3_thu-afternoon-mentor-ui-worklist_for-local-append_v1.0.md` (D-25, D-26, D-27); keduanya tunggu append ke master lokal
- Decision log sprint: `BUILD-LOG.md` di repo (D-08…D-14, D-16…D-26 + baris build s/d 17:55), PI §3.6
- **Repo code:** https://github.com/Setya78/ultrabyte-thunderhacks (private s/d submit) · HEAD 2026-10-15 ~17:56 = v0.15.0-worklist + hotfix (hash ASSUMED, owner `git log -1`); mirror governance `docs/governance/` (D-27)
- **Live URL:** https://ultrabyte.denysetya.com (v0.15.0-worklist, VERIFIED `/health` 18:00; sign-in wajib; `/v1` konsol Version 1.0; nginx `client_max_body_size 20m` untuk Import)
- **Jira:** UBP "UltraByte Project" — UBP-1…UBP-36 (5 epic); UBP-22 comments 12451/12452 (mentor, organizer, AGCO); roadmap terbuka di WD-05
- **n8n:** workflow `IUofMr1jJM47K5Di` "UltraByte - AI case summary (THX)" (published)
- **Confluence UltraByteP:** Infra Runbook (103219201) · Baseline (104529921, 104562689) — mirror; tidak ada halaman tentang fitur app, jadi tidak diubah di D-24

## 8. Cross-References & Open Items

- **Constitution:** L1-01 + L2-01 + L2-02 v1.1 + L3-01 + L3-04 v1.1 + L4-01 v1.1
- **Direction source:** A4-PER-CAR-01 · **Parent:** A2-PER-01
- **OPEN (owner verify):** label versi Workflow Standard tidak konsisten antar sumber (PI: L3-01 v1.3; scaffold: v1.2; template: v1.4). Tidak direkonsiliasi diam-diam.
- **OPEN:** port 3100 VPS (loki) terbuka ke internet — di luar scope, owner tinjau.
- **OPEN:** folder lokal owner-of-record belum disinkronkan dari Project docs sejak D-15; path folder belum ditemukan dari sesi ini (bukan di Documents/Projects/C:\dev) → owner sambungkan.
- **OPEN (lane d):** rujukan primer 4 penanda harm Safer Gambling (README: ASSUMED).
- **OPEN (lane a):** rutinitas V1 layar 3–6 (UBP-22) — follow-up ke mentor belum dijawab; tetap ASSUMED dan dilabeli.
- **OPEN (D-26):** migrasi 006 di VPS + smoke hand-off oleh owner (Kam 21:30).
- **OPEN (D-27):** salinan Project files DEMO-XLSX STALE → ganti; Demo Guide share ke tim; adegan 8 hand-off.
- **OPEN (owner):** tautan V2 → `/v1`.

## 9. Version History

| Version | Date | Change | Author |
|---|---|---|---|
| v1.0 | 2026-10-10 | Initial index | Claude (scaffold) for Owner |
| v1.1 | 2026-10-14 | + BL-MVP-01; pointer live URL & Confluence | Claude for Owner |
| v1.1 | 2026-10-14 14:53 | + LOCK-REGISTER row; D-04 | Claude for Owner |
| v1.1 | 2026-10-14 17:40 | K0 v0.6 (D-06); track (D-05); IN-03…IN-06; WD-01 | Claude for Owner |
| v1.1 | 2026-10-14 19:12 | K0 v0.7 (D-07); IN-07; WD-01 rev | Claude for Owner |
| v1.1 | 2026-10-14 21:45 | D-15 session lock: logo mark (D-14), IN-08, WD-02/03, repo HEAD + Jira pointers, BL §7 superseded; folder lokal disinkronkan | Claude for Owner |
| v1.1 | 2026-10-15 08:55 | D-21 session lock: DEMO-XLSX, WD-04 (WD-03 superseded), IN-09, LOCK-REGISTER + D-16…D-21, pointers HEAD `f4bf7b9` / v0.11.0 / n8n / Jira UBP-35, open items folder lokal + harm references | Claude for Owner |
| v1.1 | 2026-10-15 18:45 | D-28 (PART3 addendum): hand-off box every player page, dropdown filters + status, status chips; live 0.15.0 verified; LOCK-REGISTER row D-28; WD-06 handoff NEW | Claude for Owner |
| v1.1 | 2026-10-15 18:05 | D-25 + D-26 + D-27 (shard PART3): DEMO-GUIDE NEW, SKILL-LOOP NEW, DEMO-XLSX Project-files copy STALE, WD-05 demo script superseded, IN-12/13/14, LOCK-REGISTER AMEND, pointers v0.15.0-worklist / docs/governance mirror / UBP-22 comments, open items 006 + hand-off smoke + workbook replace | Claude for Owner |
| v1.1 | 2026-10-15 10:15 | D-22 + D-24 (shard PART2): DECK-V1V2 NEW, DEMO-XLSX AMEND (nama unik), WD-05 NEW (WD-04 superseded), IN-10/IN-11, LOCK-REGISTER AMEND, K0 note (toggle superseded), pointers HEAD `9a98c30` / v0.13.0-review / Jira UBP-36 / Confluence unchanged, open items V1 routine + tautan V2→/v1 | Claude for Owner |
