# VedaConnect — rules.md

Rules for humans **and** for AI coding agents. If a rule and a shortcut conflict, the rule wins.

---

## PART A — Medical & legal hard limits

| # | Rule | Why |
|---|---|---|
| A1 | **Never present an AI output as a diagnosis.** Only: possible causes, probability, confidence, urgency band, and a doctor escalation path. | Patient safety; no liability shield exists for autonomous diagnosis |
| A2 | **Every AI screen carries the disclaimer + one-tap doctor CTA, together.** A screen with the disclaimer but no CTA is a bug. | Escalation must be cheaper than believing the AI |
| A3 | **Red-flag symptoms override all AI output.** Chest pain + sweating, stroke signs (FAST), severe bleeding, breathlessness at rest, unconsciousness, suicidal ideation, pregnancy bleeding → straight to Emergency screen. No "maybe". | These are time-critical |
| A4 | **Blood: donation only, through licensed blood banks.** Never display a price, never broker, never allow a "sell" flow. Requests route to banks/donors, not to a marketplace. | Buying/selling human blood is prohibited in India |
| A5 | **Prescriptions only from registered medical practitioners**, with registration number shown. AI may draft text; a doctor must authorise. | Telemedicine Practice Guidelines 2020 |
| A6 | **No treatment guarantees.** Copy uses "indicative", "estimated", "range". | Consumer protection |
| A7 | **Minors:** under-18 accounts need guardian consent; PHI access restricted to guardian + treating doctor. | DPDP additional diligence for children |
| A8 | **No training/fine-tuning on user data** without explicit, separate, revocable consent. | DPDP purpose limitation |
| A9 | **Doctor identity verification before first consult** (reg no. + council lookup). Unverified doctors cannot be listed. | Fraud |
| A10 | **No unverified public reviews.** Feedback requires a `booking_id` in `discharged` state. | Defamation + gaming |

---

## PART B — Security rules (DPDP Act 2023 + OWASP ASVS L2)

### B1 Consent & data subject rights
- Consent before any PHI write. Consent is **free, specific, informed, revocable**; blanket consent is invalid.
- Store `consents(purpose, scope, version, granted_at, revoked_at)`. Purposes: `care_delivery`, `record_storage`, `research_anonymised`, `marketing`.
- Revocation must take effect in the same request cycle for future reads; existing audit rows stay.
- Provide Data Principal rights endpoints: access, correction, erasure (except where retention is legally required), grievance contact.
- Consent UI in the patient's language, plain language, no dark patterns (no pre-ticked boxes, reject as easy as accept).

### B2 Encryption
- TLS 1.3 in transit; HSTS with preload; no mixed content.
- AES-256-GCM application-level encryption for `intakes.raw_text`, `report_extractions.values`, `consults.notes`, `prescription` free text.
- Object storage: server-side encryption with KMS-managed keys; download URLs signed, 5-minute TTL.
- Passwords: argon2id (memory ≥ 64MB, iterations ≥ 3). Never MD5/SHA1/plain.

### B3 Identity & access
- JWT access token 15 min; refresh 7 days with rotation + reuse detection → revoke family.
- RBAC: `patient`, `caregiver`, `doctor`, `hospital_admin`, `super_admin`. Enforced **server-side on every endpoint**, not just hidden in UI.
- ABAC overlay: hospital staff can only touch rows where `resource.hospital_id == actor.hospital_id`.
- Postgres Row Level Security enabled on all PHI tables; app role is NOT superuser.
- Staff (doctor, hospital_admin, super_admin) must have MFA.
- Break-glass access for emergencies must be logged with a reason string and reviewed weekly.

### B4 Audit
- Every PHI read and write → `audit_logs` row: `actor_id, actor_role, action, resource_type, resource_id, purpose, ip_hash, ua_hash, created_at`.
- `audit_logs` is append-only: no `UPDATE`, no `DELETE`, no `TRUNCATE` grants for the app role.
- Patient-facing "Who accessed my data" screen mirrors this table.

### B5 Application hardening
- Validate every input with Pydantic v2 on the server (never trust client Zod alone).
- Parameterised queries only — no string-built SQL.
- Rate limits: `/auth/login` 5 per 15 min per IP+phone; `/intake` 20/h; `/attachments` 30/h; `/blood/requests` 10/h.
- Signed + single-use QR tokens; store only `sha256(token)`.
- File uploads: allow-list MIME (`image/jpeg,image/png,application/pdf`), max 10 MB, magic-byte check, re-encode images server-side, strip EXIF.
- CSP: no `unsafe-inline`; SRI on third-party scripts.
- Dependency scanning (Dependabot + `pip-audit` + `npm audit`) must pass in CI.
- Secrets only from environment/secret manager. A secret in git = rotate immediately.

### B6 Logging & analytics
- **Never** log: names, phone numbers, addresses, symptoms, report values, tokens, file URLs.
- Logger middleware applies a PHI scrubber before emit.
- Analytics events use IDs and enum values only. Free text is never sent.
- Sentry: `beforeSend` strips request bodies and query strings.

---

## PART C — Coding rules

### C1 What to do
- TypeScript `strict: true`. No `any` (use `unknown` + Zod parse).
- Feature-sliced folders: everything for `F04` lives in `features/hospital-finder/`.
- Every network call goes through `lib/api/client.ts` (adds auth, refresh, error normalisation, timeout).
- Server state via TanStack Query only; no `useEffect` fetching.
- All strings through `t('key')` — **zero hardcoded English in JSX.** Ship `en` as source of truth; other locales via Bhashini with human review for medical terms.
- Every async UI has 4 explicit states: `loading`, `empty`, `error`, `success` — plus `stale` for availability data.
- Errors: `ErrorBoundary` at route level; toasts for recoverable, full page for fatal, and always a human-readable next step.
- Money as integer paise; dates as UTC ISO in DB, localised at render; never `new Date(string)` without a parser.
- Accessibility: semantic HTML, labelled inputs, `aria-live` for status changes, focus trap in modals, 48px targets.
- Tests: unit for services (`care_score`, `finance`, red-flag classifier), integration for auth + booking, one Playwright happy path per phase.

### C2 What to avoid
- ❌ Adding a UI library on top of the existing one (Tailwind + shadcn is the decision).
- ❌ `localStorage` for PHI or tokens. Tokens in memory + httpOnly refresh cookie.
- ❌ Business logic in components; it belongs in `services/` (server) or a hook.
- ❌ Silent `catch {}`. Every catch logs a scrubbed event and surfaces a recoverable message.
- ❌ One 900-line component. Split at 200 lines or at the second concern.
- ❌ Direct DB calls from the frontend (no anon Supabase RLS writes for PHI).
- ❌ AI calls from the browser — the API key must never reach the client.
- ❌ Placeholder data shipped to prod ("Lorem", "Test Hospital").
- ❌ Feature flags implemented as commented-out code.

### C3 AI boundaries (for coding agents building AI features)
1. Model output **must** be JSON-schema validated; on parse failure → safe fallback ("We couldn't assess this — please consult a doctor").
2. Temperature ≤ 0.2 for any clinical-adjacent output.
3. Prompt must include: role limit, "do not diagnose", required fields, and refusal behaviour.
4. Log `model_version` with every assessment for reproducibility.
5. Never send PHI to a model provider without a DPA and a documented no-training configuration.
6. Confidence < 0.55 → force the "uncertain, consult a doctor" branch.
7. Human-in-the-loop: doctor annotation of an AI result is stored, never auto-accepted.

### C4 Git & release
- Conventional commits: `feat(F06): ...`, `fix(blood): ...`, `chore: ...`.
- One PR = one phase task from phases.md. PR must include: screenshots, acceptance-test evidence, and a `memory.md` update.
- `main` is protected; no direct pushes; CI must be green.
- Every PR touching PHI tables needs a labelled `security-review`.

---

## PART D — Design/UX rules (short form; detail in design.md)

- One primary action per screen. Max 3 visible choices on a patient screen.
- Base font 18px; patient-facing content never below 16px.
- Colour is never the only signal (icon + text + colour together).
- Emergency is always red, always reachable in ≤ 2 taps, always present.
- Every destructive or money action needs a confirm step written in the patient's language.
- No auto-playing video, no carousels, no modal on first load except consent.
- Text expansion: layouts must survive +30% string length (Tamil/Telugu/Malayalam are long).
