# VedaConnect — architecture.md

**Strategy:** extend the existing CHIKITSA-X monorepo. Keep React 19 + Vite + FastAPI + SQLAlchemy. Replace SQLite with PostgreSQL (Supabase), add Realtime, object storage, and a worker queue.

---

## 1. System diagram

```
┌──────────────────────────────────────────────────────────────┐
│  CLIENT (PWA)  React 19 + TS + Vite + Tailwind                 │
│  ├─ Patient / Caregiver app                                    │
│  ├─ Doctor workspace                                           │
│  ├─ Hospital admin console                                     │
│  └─ i18n layer (Bhashini)  ·  Map layer (Google Maps JS)       │
└───────────────┬──────────────────────────────────────────────┘
                │ HTTPS / JSON  (JWT access 15m + refresh 7d rotation)
┌───────────────▼──────────────────────────────────────────────┐
│  API  FastAPI (uvicorn, async) — /api/v1                       │
│  ├─ auth   ├─ patients  ├─ hospitals  ├─ bookings              │
│  ├─ intake ├─ reports   ├─ journey    ├─ blood                 │
│  ├─ consult├─ feedback  ├─ reminders  └─ admin                 │
│  ├─ RBAC dependency + audit middleware                         │
│  └─ integrations: Places, Bhashini, LLM-Vision, OCR, FCM       │
└───┬───────────────┬───────────────────┬────────────────────────┘
    │               │                   │
┌───▼────┐   ┌──────▼──────┐   ┌────────▼─────────┐
│Postgres│   │ Redis       │   │ S3-compatible    │
│(Supabase│  │ cache +     │   │ object store     │
│ + RLS) │   │ ARQ queue   │   │ (SSE-KMS, PHI)   │
└───┬────┘   └──────┬──────┘   └──────────────────┘
    │               │
    │               └──► worker: OCR, image triage, reminders,
    │                           report parsing, push fanout
    └──► Supabase Realtime (Postgres logical replication)
         → channels: hospital:{id}, patient:{id}, booking:{id}
```

---

## 2. Tech stack (final)

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 19 + TypeScript + Vite | Already in CHIKITSA-X |
| Styling | Tailwind CSS + shadcn/ui + CSS vars from design.md | Speed + token discipline |
| State | TanStack Query (server) + Zustand (UI) | Cache + realtime invalidation |
| Routing | React Router 7, role-guarded layouts | Simple |
| Forms/validation | react-hook-form + Zod (shared schema with backend) | One source of truth |
| i18n | i18next + Bhashini translate API, cached per (string, lang) | 22 scheduled languages |
| Maps | Google Maps JS + Places API (New) + Street View Static | Exact pins + entrance preview |
| Charts | Recharts | Dashboards |
| Backend | FastAPI + Pydantic v2 + SQLAlchemy 2.0 (async) + Alembic | Existing |
| DB | PostgreSQL 16 on Supabase (SQLite only for local tests) | Realtime + RLS |
| Realtime | Supabase Realtime (Postgres changes) + `postgres_changes` filters | No separate socket server |
| Queue | Redis + ARQ (async) | Light, Python-native |
| Auth | JWT (argon2id hashing), access 15m / refresh 7d rotation, MFA for staff | Rules |
| Files | S3-compatible (Supabase Storage / R2), server-side encryption, signed URLs 5 min | PHI |
| AI – triage | Gemini 2.x / GPT-4o vision, structured JSON output, confidence + red-flag guard | Probabilistic only |
| AI – OCR | Google Cloud Vision (primary) → Tesseract (fallback) | Report analyzer |
| Voice | Bhashini ASR/TTS (Indian languages) + Web Speech API fallback | F02, F06 |
| Push | FCM (web push) + WhatsApp Cloud API | Reminders |
| Video | LiveKit / 100ms | Teleconsult |
| Observability | Sentry (PHI-scrubbed) + OpenTelemetry + structured JSON logs | Ops |
| CI/CD | GitHub Actions → Vercel (FE) + Render/Fly (API) + Supabase (DB) | Fast |

**Realtime decision:** Supabase Realtime uses Postgres logical replication to broadcast row changes, which fits our "one source of truth, zero custom socket code" need better than Firebase for a relational clinical schema.

---

## 3. Repository / folder structure

```
vedaconnect/
├─ prd.md  architecture.md  rules.md  phases.md  design.md  memory.md
├─ apps/
│  ├─ web/                        # React 19 + Vite
│  │  ├─ src/
│  │  │  ├─ app/                  # router, providers, layouts
│  │  │  │   ├─ routes.tsx
│  │  │  │   └─ guards/{RoleGuard,ConsentGuard}.tsx
│  │  │  ├─ features/             # feature-sliced, one folder per F-id
│  │  │  │   ├─ emergency/
│  │  │  │   ├─ hospital-finder/
│  │  │  │   ├─ intake/
│  │  │  │   ├─ reports/
│  │  │  │   ├─ journey/
│  │  │  │   ├─ blood/
│  │  │  │   ├─ consult/
│  │  │  │   ├─ reminders/
│  │  │  │   ├─ feedback/
│  │  │  │   └─ dashboards/{patient,doctor,hospital,admin}/
│  │  │  ├─ components/ui/        # shadcn primitives + Veda* wrappers
│  │  │  ├─ lib/
│  │  │  │   ├─ api/client.ts     # fetch wrapper, token refresh
│  │  │  │   ├─ i18n/{index.ts,locales/*.json}
│  │  │  │   ├─ maps/places.ts
│  │  │  │   ├─ realtime/channels.ts
│  │  │  │   └─ analytics/scrub.ts
│  │  │  ├─ styles/tokens.css
│  │  │  └─ main.tsx
│  │  └─ public/  (logo.svg, icons, manifest.webmanifest)
│  └─ api/                        # FastAPI
│     ├─ app/
│     │  ├─ main.py
│     │  ├─ core/{config,security,rbac,audit,errors,logging}.py
│     │  ├─ db/{base,session,models/,migrations/}
│     │  ├─ api/v1/{auth,patients,hospitals,bookings,intake,reports,
│     │  │          journey,blood,consult,feedback,reminders,admin}.py
│     │  ├─ services/{triage,ocr,places,bhashini,care_score,
│     │  │            finance,notify,storage,blood}.py
│     │  ├─ workers/{tasks.py, arq_settings.py}
│     │  └─ schemas/              # Pydantic, mirrors Zod
│     └─ tests/{unit,integration}/
└─ packages/
   └─ shared/                     # generated TS types from OpenAPI
```

**Rule:** a feature folder owns its components, hooks, types, API calls and tests. No cross-feature imports except through `components/ui` and `lib`.

---

## 4. Data model (core tables)

```
users(id, role[patient|caregiver|doctor|hospital_admin|super_admin],
      phone, email, password_hash, mfa_secret, lang, created_at, deleted_at)

consents(id, user_id, purpose, scope, version, granted_at, revoked_at)

patient_profiles(user_id, dob, sex, blood_group, allergies, chronic[], abha_opt_in)

hospitals(id, name, reg_no, verified, phone, email,
          lat, lng, place_id, formatted_address,
          pin_verified_by, pin_verified_at, streetview_heading,
          emergency_24x7, trauma_icu, services[], specialties[],
          opd_fee_min, opd_fee_max, updated_at)

hospital_staff(id, hospital_id, user_id, designation)

beds(id, hospital_id, ward, total, occupied, updated_at)
availability_signals(id, hospital_id, service, status, observed_at, source)

doctors(id, user_id, hospital_id, reg_no, specialties[], fee, langs[], verified)

bookings(id, patient_id, hospital_id, doctor_id, slot_at, token_no,
         status[prebooked|checked_in|in_consult|admitted|discharged|cancelled],
         ref_id, qr_token_hash, created_at, updated_at)

journey_events(id, booking_id, type[opd|bed|medication|procedure|discharge],
               payload_json, actor_id, created_at)

intakes(id, patient_id, mode[text|voice], raw_text, lang,
        extracted jsonb, concern_level, red_flags[], model_version, created_at)

attachments(id, owner_id, kind[report|photo|prescription], storage_key,
            sha256, mime, ocr_status, retention_until)

report_extractions(id, attachment_id, raw_text, values jsonb,
                   confidence jsonb, ai_summary_i18n jsonb)

image_assessments(id, attachment_id, candidates jsonb,
                  confidence, urgency_band, disclaimer_version, reviewed_by_doctor)

blood_banks(id, name, licence_no, lat, lng, phone, place_id, verified)
blood_stock(id, bank_id, group, units, updated_at)
donors(user_id, blood_group, last_donation_at, eligibility_status, consent_share)
blood_requests(id, requester_id, booking_id, group, units, urgency,
               hospital_id, status, fulfilled_by_bank_id)

reminders(id, patient_id, drug, dose, schedule_cron, tz, source,
          active, last_fired_at)
reminder_logs(id, reminder_id, fired_at, status[taken|skipped|no_response])

consults(id, booking_id, room_id, starts_at, ended_at, notes, prescription_id)

feedback(id, booking_id, patient_id, rating, text, before_after_opt_in,
         verified_visit, moderation_status, created_at)

audit_logs(id, actor_id, actor_role, action, resource_type, resource_id,
           purpose, ip_hash, ua_hash, created_at)   -- append-only, no UPDATE grant
```

**Invariants**
- `audit_logs` has no UPDATE/DELETE grants for the app role.
- PHI columns (`raw_text`, `extracted`, `values`) are encrypted at application level with a KMS-held key.
- `bookings.ref_id` is the only identifier printed on a QR code; the raw token is never stored.

---

## 5. Key API surface (`/api/v1`)

```
POST   /auth/register            POST /auth/login     POST /auth/refresh
POST   /auth/mfa/verify          POST /auth/logout
GET    /me                       PATCH /me            PATCH /me/language

GET    /hospitals?lat&lng&need&budget&lang&sort=care_score
GET    /hospitals/{id}           GET  /hospitals/{id}/availability
PATCH  /hospitals/{id}           # admin only, writes audit
POST   /hospitals/{id}/pin-verify

POST   /intake                   POST /intake/{id}/answer
POST   /attachments              # signed upload URL
POST   /attachments/{id}/analyze?kind=image|report
GET    /reports/{id}/explain?lang=ta

POST   /bookings                 GET  /bookings/{id}   POST /bookings/{id}/cancel
POST   /bookings/{id}/checkin    POST /bookings/{id}/journey-events
GET    /bookings/{id}/journey

GET    /blood/banks?lat&lng&group      GET /blood/stock?bank_id
POST   /blood/requests                 POST /blood/donors
GET    /blood/eligibility?last_donation_at

POST   /reminders                GET /reminders/upcoming
POST   /consults/{booking_id}/room
POST   /feedback                 GET /feedback?hospital_id&verified_only=true

GET    /admin/audit?resource_id   GET /admin/hospitals/pending
GET    /healthz                  GET /metrics
```

Realtime channels (Supabase): `hospital:{id}`, `booking:{id}`, `patient:{id}`, `blood:{bank_id}`, `admin:queue`.

---

## 6. Critical flows

### 5.1 Emergency path (must never fail)
1. Tap red pill → `GET /hospitals?lat&lng&need=emergency&radius=15km`.
2. Rank by **ETA** (distance matrix) then capability (trauma ICU, 24×7, blood group in stock).
3. Render: name, exact address, distance, ETA, tap-to-call, `google.navigation` deep link.
4. If Places API is down → fall back to cached local dataset (last 24h) so the page still renders.

### 5.2 Image triage (probabilistic, gated)
```
upload → worker → {image → vision model (structured JSON)}
      → guard: if red_flags OR urgency=now → force emergency CTA
      → store candidates[{condition, probability}] + confidence
      → UI: "Possible causes (not a diagnosis)" + confidence badge
            + [Talk to a doctor] + [Go to emergency] + disclaimer vX
```
Never render a single condition name as a verdict. Doctor can annotate → `reviewed_by_doctor`.

### 5.3 Report analyzer
```
camera/pdf → OCR (Vision) → per-field confidence
  → patient confirms low-confidence fields
  → LLM explains each parameter in patient's language with reference range
  → "Questions to ask your doctor" list
```

### 5.4 Realtime prop
Hospital admin edits `beds` / `formatted_address` / `services` →
Postgres `UPDATE` → Supabase Realtime → subscribed patient + doctor screens
invalidate relevant TanStack Query keys → UI reflects within 2s p95.
**Staleness rule:** any `availability_signals.observed_at` older than 6h renders as
"Last verified 6h ago" and drops out of Care Score availability weight.

### 5.5 Map accuracy pipeline
```
Places Autocomplete (name only)
   → Place Details(New): place_id, location{lat,lng}, formatted_address,
     international_phone_number, photos, business_status
   → hospital row stores place_id + lat/lng + full address
   → Street View Static API with heading → "Simulation" preview card
   → admin must confirm pin once (pin_verified_by/at) ⇒ verified badge
```
Non-Google fallback: Leaflet + OSM tiles + Nominatim, marked "Unverified location".

---

## 7. Security architecture (summary — full rules in rules.md)

- TLS 1.3 everywhere; HSTS preload.
- PHI at rest: AES-256-GCM application-level for `intakes.raw_text`, `report_extractions.values`, `attachments` (server-side encryption).
- Row Level Security in Postgres: patient can read only their own rows; hospital role scoped to `hospital_id`.
- JWT: access 15m, refresh 7d with rotation + reuse detection; staff MFA mandatory.
- Rate limits: `/intake` 20/h, `/attachments` 30/h, `/auth/login` 5/15m per IP+phone.
- No PHI in logs/analytics/Sentry — scrubber at the logger boundary.
- Signed upload/download URLs, 5 min TTL.
- Immutable audit log for every PHI read (actor, purpose, resource).

---

## 8. Environments & deployment

| Env | Frontend | API | DB |
|---|---|---|---|
| local | Vite :5173 | uvicorn :8000 | Postgres via Docker |
| staging | Vercel preview | Render | Supabase (staging project) |
| prod | Vercel | Render (2 instances, health-checked) | Supabase (Mumbai region) |

Mumbai region for data residency. Daily PITR backups, 30-day retention, quarterly restore drill.

---

## 9. Observability

- `/healthz` (liveness), `/readyz` (DB + Redis + storage).
- Golden-path alerts: emergency search error rate, triage p95 latency, realtime lag, OCR failure rate.
- Product analytics: funnel events only, no free-text PHI.
