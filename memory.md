# VedaConnect — memory.md

Living state file for AI coding agents (Cursor / Claude Code / Windsurf / Lovable / TRAE).
**Update this file at the end of every working session. It is the first file an agent reads.**

---

## How to use this file

1. An agent **reads memory.md before writing any code**.
2. It picks up exactly one incomplete item under "Current work".
3. On finishing, it appends to "Completed", rewrites "Current work", and records new decisions.
4. Never delete history — move it down. The log is append-only like our audit table.

---

## Project snapshot

| Field | Value |
|---|---|
| Project | **VedaConnect** — Connected Healthcare for Everyone |
| Base repo | `Rahul-Gupta-Dev/CHIKITSA-X` (upgrade, not rewrite) |
| Current phase | **Phase 1 — Clinical Logic & AI Integration** (Complete) |
| Current file being worked | `backend/app/services/gemini_service.py` & `routers/ai_analyzer.py` |
| Blocking issue | none |
| Last updated | 2026-11-03 |
| Stack | React 19 + TS + Vite + Tailwind · FastAPI + SQLAlchemy 2.0 + Neon PostgreSQL · Google Gemini 3.5 Flash |
| Deploy | Localhost (:5173 / :8000) · Neon Cloud DB |

---

## Current work

- [x] Phase 0.1 — Neon PostgreSQL connected & verified
- [x] Phase 0.3 — 38 tables initialized (all Veda models: veda_bookings, veda_consents, veda_audit_logs, beds, blood_banks, reminders, etc.)
- [x] Phase 0.5 — `core/security.py` → Argon2id password hashing + dual token (access 15m / refresh 7d rotation + reuse detection)
- [x] Phase 0.5 — `core/logging_config.py` structured JSON logging + PHI scrubber (phone, email, aadhaar-like)
- [x] Phase 0.5 — `core/rbac.py` role-based & hospital ABAC access control
- [x] Phase 0.5 — `core/errors.py` standardized error envelope
- [x] Phase 0.5 — `routers/auth_v2.py` `/api/v1/auth/*` (register, login, refresh, logout, me)
- [x] Phase 1.3 — `services/care_score.py` (5-vector engine: 35/25/15/15/10) with 6h staleness & sponsored exclusion
- [x] Phase 1.4 — `services/veda_triage_service.py` with deterministic red-flag guard
- [x] Phase 1.5 — `routers/hospitals_v2.py` Care Score ranking & breakdown
- [x] Phase 1.6 — `routers/bookings.py` Hashed QR token & immutable journey events
- [x] Phase 1 Tests — 57 / 57 unit tests passed
- [x] AI Integration — Google Gemini 3.5 Flash connected (`gemini_service.py` & `routers/ai_analyzer.py`)
  - Lab Report Analyzer with simple Hindi/English summaries & 3 doctor questions
  - Probabilistic Image Triage (dermatology/wound)
  - Multilingual natural symptom intake
- [ ] Phase 0.6 / Phase 2.1 — Frontend i18n scaffold & Calm UI Integration

## Next up (queued)

- Phase 0.6 i18n frontend scaffold
- Phase 1.3 `services/care_score.py` + unit tests
- Phase 1.4 `services/triage.py` + red-flag guard
- Phase 2.1 Calm UI shell (Emergency + Hospital Finder)

---

## Completed

### 2026-11-03 — Planning documents
- ✅ `prd.md` — positioning, 5 problems, personas, 16 features with problem/monetisation/MVP tag, rejection log, NFRs, metrics, monetisation, compliance boundaries
- ✅ `architecture.md` — system diagram, final stack, folder structure, data model, API surface, 5 critical flows, security architecture, deployment
- ✅ `rules.md` — medical/legal limits (A1–A10), DPDP + OWASP security rules (B1–B6), coding do/avoid + AI boundaries (C1–C3), design rules
- ✅ `design.md` — logo-derived colour tokens, typography incl. 9 Indic script fonts, "One Thing Per Screen" layout, component specs, a11y, copy tone
- ✅ `phases.md` — Phase 0–10 with acceptance tests, copy-paste IDE prompts, feature traceability, definition of done
- ✅ Existing CHIKITSA-X audited: 9 features, React 19 + FastAPI + SQLite, mock services for voice/OCR/triage
- ✅ Blood module corrected to donation-only via licensed banks (selling prohibited)

### Carried from CHIKITSA-X (already built, keep)
- Care Score 5-vector engine, QR OPD pass + hashed token, consent protocol, doctor workspace, cost estimate generator, financial gap engine, emergency modal
- **Debt to fix:** SQLite → Postgres, `localStorage` PHI removal, mock OCR/triage → real services, no RLS, no i18n, no realtime

---

## Decisions log (ADR-lite)

| # | Date | Decision | Why | Rejected alternative |
|---|---|---|---|---|
| D1 | 2026-11-03 | Postgres + Supabase Realtime over Firebase | Relational clinical schema + RLS + logical-replication realtime | Firebase (no SQL joins, weak RLS) |
| D2 | 2026-11-03 | Bhashini for 22 scheduled languages | Government-backed, covers all 22, includes ASR/TTS/OCR | Google Translate (weaker Indic voice, cost) |
| D3 | 2026-11-03 | AI = probabilistic triage, never diagnosis | Safety + legal liability | "AI detects disease from photo" |
| D4 | 2026-11-03 | Blood = donation only via licensed banks | Selling blood is illegal in India | Donor marketplace with pricing |
| D5 | 2026-11-03 | Google Places (New) as source of truth for geo | Exact pin + `formatted_address` + `place_id` stability | OSM only (kept as labelled fallback) |
| D6 | 2026-11-03 | Calm UI enforced as a rule, not a preference | Sick/anxious users cannot parse dense portals | Multi-service portal like Practo |
| D7 | 2026-11-03 | Doctor workspace + hospital admin from Phase 4 | Realtime value only exists once both dashboards exist | Patient-only MVP |
| D8 | 2026-11-03 | Append-only `audit_logs` with no UPDATE grant | DPDP accountability | App-level delete |

---

## Open questions

| # | Question | Owner | Needed by |
|---|---|---|---|
| Q1 | Hospital verification source — state health dept registry vs manual doc upload? | Rahul | Phase 4 |
| Q2 | Blood bank partnerships: which licensed banks first (Delhi NCR)? | Rahul | Phase 8 |
| Q3 | Teleconsult legal entity + doctor empanelment model (own clinic vs partner) | Rahul | Phase 9 |
| Q10 | WhatsApp Business API provider (Meta direct vs Gupshup/Gupshup-like) | Dev | Phase 10 |
| D8 | Do we seed 500 hospitals manually or Places-only for launch city? | Rahul | Phase 2 |

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Places API cost blow-up from autocomplete | ₹ burn | Session tokens, debounce 400ms, cache 24h |
| AI false negative on a real emergency | Harm | Deterministic red-flag guard runs before model; emergency always 2 taps away |
| LLM hallucinating a disease name | Legal | JSON schema + banned-phrase check in output validator |
| Supabase Realtime channel sprawl | Perf | One channel per entity id, unsubscribe on unmount |
| Indic font bundle bloating LCP | UX | Per-locale dynamic font import, `font-display: swap` |
| Hospital data going stale | Wrong care decision | 6h staleness rule → "Last verified" badge, drops from Care Score |

---

## Session template (copy at the end of each session)

```md
### YYYY-MM-DD — <agent/tool name>
**Worked on:** <phase.item>
**Changed:** <files>
**Why:** <one line>
**Tests:** <passing / failing, which>
**Next:** <single next item>
**Blocked by:** <none | issue>
```
