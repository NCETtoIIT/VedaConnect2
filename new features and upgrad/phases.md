# VedaConnect — phases.md

**Build order rule (from your notebook):** Idea → Planning → Market → Branding → PRD → **Backend first** → Auth (JWT) → then feature-by-feature frontend → Dashboard last → Polish.
**Never build two phases in one go.** Each phase ends with a green acceptance test and a `memory.md` update.

---

## Phase 0 — Setup & foundations (2–3 days)

| Step | Task | Done when |
|---|---|---|
| 0.1 | Clone CHIKITSA-X, branch `veda-v2` | Repo runs locally |
| 0.2 | `.env.example` with all keys: `DATABASE_URL, JWT_SECRET, JWT_REFRESH_SECRET, GOOGLE_MAPS_KEY, BHASHINI_API_KEY, SUPABASE_URL, SUPABASE_*_KEY, LLM_API_KEY, S3_*` | No secret in git |
| 0.3 | Postgres via Docker locally; `alembic init`; migration `0001_init` | `alembic upgrade head` succeeds |
| 0.4 | Tailwind + tokens.css from design.md; shadcn init; fonts loaded | Storybook-less style page renders |
| 0.5 | `core/` — config, logging with PHI scrubber, error envelope, RBAC dependency, audit middleware | Unit tests pass |
| 0.6 | i18n scaffold: `en` + `hi`, `t()` in every component, language switcher shell | Switching to Hindi changes nav labels |
| 0.7 | Sentry + `/healthz` + CI (lint, typecheck, tests, pip-audit) | Red CI blocks merge |

**Prompt to paste into your IDE (Cursor / Claude Code / Windsurf):**

```
Read prd.md, architecture.md, rules.md and design.md in this repo.
Task: Phase 0 setup only.
1. Convert the FastAPI SQLite setup to async PostgreSQL with Alembic; create migration 0001_init
   containing the tables listed in architecture.md §4 with RLS policies for patient/hospital scope.
2. Add app/core: config.py (pydantic-settings), security.py (argon2id, JWT access 15m + refresh 7d
   rotation with reuse detection), rbac.py (role dependency + hospital ABAC check), audit.py
   (append-only writer), logging.py (JSON logs + PHI scrubber), errors.py (consistent error envelope).
3. Add the i18n scaffold with i18next, en.json + hi.json, and a LanguageSwitcher component.
Do not build any feature UI yet. Output: file tree, migration file, and a curl test proving
login → refresh → authorised GET works.
```

---

## Phase 1 — Logic layer (backend only, no pretty UI) — **your notebook's "Phase 1: Logic"**

Goal: every feature's brain works and is testable via API before a single pixel exists.

| Step | Feature | Endpoints | Acceptance test |
|---|---|---|---|
| 1.1 | Auth + roles | `/auth/*`, `/me` | 5 roles can register; patient cannot call admin route (403); refresh rotation revokes old token |
| 1.2 | Hospitals CRUD + geo | `/hospitals` | lat/lng + `formatted_address` stored exactly from Places; unknown `place_id` rejected |
| 1.3 | **Care Score** service | `GET /hospitals?sort=care_score` | Unit test: 5 vector weights sum to 100; each result exposes breakdown; sponsored excluded |
| 1.4 | **Triage** service | `POST /intake` | Red-flag input → `concern_level=emergency`; JSON schema validated; invalid JSON → safe fallback |
| 1.5 | Booking + QR token | `/bookings` | Token stored as sha256 only; ref_id `VC-2026-XXXXX` unique |
| 1.6 | Consent + audit | `/consents`, `audit_logs` | Every PHI read writes a row; UPDATE on audit_logs blocked by DB grant |
| 1.7 | Availability + staleness | `/hospitals/{id}/availability` | Row older than 6h returned with `stale=true` |

**Prompt:**

```
Phase 1 — backend logic only. Implement services/ per architecture.md and rules.md:
- services/care_score.py: 5-vector scoring (clinical_fit 35, affordability 25, distance 15,
  availability 15, support 10), returns total + breakdown dict. Pure function, fully unit-tested.
2. services/triage.py: strict JSON schema {symptoms[], duration, severity, red_flags[],
   concern_level, suggested_specialty, confidence}. Include a deterministic red-flag guard that
  runs BEFORE the model and can only escalate. Temperature <= 0.2.
3. services/places.py: Places API (New) Text Search + Place Details, normalise to
   {name, place_id, lat, lng, formatted_address, phone, photos[]}; 24h cache.
4. Auth, booking with hashed QR token, audit middleware, RBAC dependency.
Deliver pytest tests for each service. No React changes in this phase.
```

---

## Phase 2 — Calm UI shell + Emergency + Hospital finder (MOST IMPORTANT phase)

This is the phase that proves the whole thesis. If a sick, anxious person cannot finish this in 60 seconds, nothing else matters.

| Step | Task | Acceptance test |
|---|---|---|
| 2.1 | App shell: header (logo, language, emergency pill), 3-tile home, no carousel | Home has exactly 3 primary actions |
| 2.2 | Emergency screen | Cold load → callable hospital in ≤ 2 taps; works with Places down (cache fallback) |
| 2.3 | Finder: search, location permission, filters (need, budget, distance) | Result pin == Places pin; address string byte-identical to `formatted_address` |
| 2.4 | Hospital detail: map, Street View "simulation", Care Score breakdown panel, call, navigate | "Why recommended?" opens with per-vector bars |
| 2.5 | Places-unavailable fallback (Leaflet/OSM) labelled "Unverified location" | Fallback renders and never claims verified |
| 2.6 | i18n pass: hi, ta, te, bn, mr on these screens | Long-string layout does not break (+30%) |

**Prompt:**

```
Phase 2 — patient Calm UI. Build features/emergency and features/hospital-finder only.
Constraints (rules.md Part D): one primary action per screen, max 3 choices, base 18px,
48px touch targets, no carousel, no first-load modal except consent, colour never the only signal.
Emergency: red pill in header on every route → /emergency → list ranked by ETA
(distance matrix) then capability (24x7, trauma_icu, blood group in stock), each card with
name, full formatted_address, distance, ETA, Call, Navigate deep link, and Street View thumbnail.
Finder: search by name or need, geolocation, filters, results with Care Score + breakdown drawer.
All strings via t(); layouts must survive +30% text expansion.
Write a Playwright test: cold load → emergency card visible with a tel: link within 3s.
```

---

## Phase 3 — Intake → Booking → Feedback loop (MVP complete)

| Step | Task | Acceptance test |
|---|---|---|
| 3.1 | Symptom intake (text + voice) multi-step, one question per screen | Voice in Hindi produces structured intake; user can edit every field |
| 3.2 | Triage result screen: concern level, specialty, disclaimer, "Book now" / "Emergency" | Red flag never shows a "wait at home" option |
| 3.3 | Booking flow: hospital → doctor → slot → confirm → QR pass | QR encodes ref_id only; token never in URL |
| 3.4 | My appointments + cancel | Cancel frees slot within 1 request |
| 3.5 | Results & feedback page: before/after gallery, rating cards, verified-visit badge | Rating impossible without `discharged` booking |
| 3.6 | Financial gap engine (ported from CHIKITSA-X) | Formula displayed as arithmetic steps |

**Prompt:**

```
Phase 3 — complete the patient loop. Build features/intake, features/bookings, features/feedback,
and port the financial gap engine from the existing frontend into services/finance.py.
Intake: one question per screen, progress indicator, voice button (Bhashini ASR), "skip" always
available, all extracted fields editable. Result screen must render disclaimer + doctor CTA + emergency
CTA together (rules A2). Booking: 4 steps, QR pass containing ref_id only. Feedback: only verified
visits, moderation queue for text > 0 chars. Add integration tests for booking → checkin → discharge
→ feedback eligibility.
```

---

## Phase 4 — Dashboards (Patient / Doctor / Hospital admin)

Your notebook's "Phase 2: Dashboard".

| Step | Task | Acceptance test |
|---|---|---|
| 4.1 | Role router + guards | Wrong role → 403 page, not blank screen |
| 4.2 | Patient dashboard | Shows journey, reminders, reports, past visits in one scroll |
| 3.3 | Doctor workspace: queue, patient 360, prescribe, mark journey events | Doctor sees triage + OCR + history in ≤ 2 clicks |
| 3.4 | Hospital admin: beds, services, address/pin verify, emergency toggle, blood stock | Saving address updates patient-facing card |
| 4.5 | Super admin: hospital verification, audit viewer, dispute queue | Audit viewer read-only and paginated |

---

## Phase 5 — Real-time layer

| Task | Acceptance test |
|---|---|
| Supabase Realtime channels: `hospital:{id}`, `booking:{id}`, `patient:{id}` | Admin changes bed count → patient card updates ≤ 2s p95 without refresh |
| Reconnect + missed-event recovery (refetch on reconnect) | Kill network 30s → state correct after reconnect |
| Optimistic UI + rollback on error | Failed update reverts and shows a toast |

```
Phase 5 — realtime. Wire Supabase Realtime (postgres_changes) into lib/realtime/channels.ts,
invalidate TanStack Query keys per channel, handle reconnect + refetch, and show
"Live" / "Reconnecting..." / "Last verified 6h ago" states. No polling loops.
```

---

## Phase 6 — Medical report analyzer (OCR)

| Task | Acceptance test |
|---|---|
| Upload (camera/PDF) → signed URL → worker OCR → per-field confidence | 10 MB PDF accepted, 11 MB rejected, EXIF stripped |
| Patient confirms low-confidence fields | Fields < 0.8 confidence visually flagged and editable |
| Plain-language explainer in patient's language + "questions to ask your doctor" | Output includes reference ranges; disclaimer present |

---

## Phase 7 — Image triage (probabilistic, gated)

| Task | Acceptance test |
|---|---|
| Photo upload → worker → vision model → candidates[] + confidence + urgency band | Never returns a single definitive disease name |
| Confidence < 0.55 → "uncertain, consult a doctor" branch | Unit test on guard |
| Doctor can annotate an assessment | Annotation stored, never auto-accepted; `reviewed_by_doctor` set |

```
Phase 7 — image triage. Prompt the vision model for JSON {candidates:[{condition, probability}],
confidence, urgency_band, visible_features[], red_flags[]}. Enforce: probabilities sum ~1,
no single-verdict phrasing, mandatory disclaimer_version, low-confidence guard at 0.55,
red-flag guard routes to Emergency. UI copy must read "Possible causes (not a diagnosis)".
Add a test that a chest-pain text intake + wound photo never bypasses Emergency routing.
```

---

## Phase 8 — Blood bank module

| Task | Acceptance test |
|---|---|
| Blood bank directory (licensed only) + stock display | Licence number required and shown; no price field exists anywhere |
| Donor registration + eligibility quiz + camp discovery | Eligibility rules applied (age/weight/interval) |
| Blood request broadcast to banks + nearby eligible donors | Request has urgency, hospital, units; no payment step |

> Blood is donation-only via licensed blood banks. Selling is prohibited by law — this is enforced structurally (no price column, no checkout route).

---

## Phase 9 — Teleconsultation

LiveKit room, waiting room with device test, 10-min slot, visit summary; prescription only by verified doctor with reg no.; recording off by default with explicit consent.

---

## Phase 10 — Medicine reminders, accessibility & hardening

| Task | Acceptance test |
|---|---|
| Reminders from prescription OCR or manual; Web Push + WhatsApp | Fires ±2 min; adherence log opt-in |
| WCAG 2.2 AA audit, 22-language QA sweep | axe-core zero critical; screenshots of 6 languages |
| Security: pen-test checklist, RLS verification, rate limits, dependency audit | OWASP ASVS L2 self-assessment signed off |
| Performance: LCP < 2.5s on throttled 4G | Lighthouse mobile ≥ 85 |

---

## Phase → feature traceability

| Phase | Features delivered |
|---|---|
| 1 | F05, F07(backend), F15, F16 (logic) |
| 2 | F01, F03, F04, F05 (UI) |
| 3 | F06, F13, F15 (UI) |
| 4 | F08, F09 (dashboards) |
| 5 | F14 |
| 6 | F07 |
| 7 | F06a |
| 8 | F10 |
| 9 | F12 |
| 10 | F11 + hardening |

---

## Definition of done (every phase)

1. Acceptance tests in this file pass, with evidence (screenshot / test output) in the PR.
2. No hardcoded English in JSX; no PHI in logs.
3. `memory.md` updated with: what shipped, current file, next step, open risks.
4. Emergency path still reachable in ≤ 2 taps from every new screen (regression check).
5. Every new AI feature ships with its disclaimer + doctor CTA in the same PR.
