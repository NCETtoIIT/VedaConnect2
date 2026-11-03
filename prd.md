# VedaConnect — Product Requirements Document (PRD)

**Version:** 2.0
**Owner:** Rahul Gupta
**Last updated:** 03 Nov 2026
**Base codebase:** CHIKITSA-X (https://github.com/Rahul-Gupta-Dev/CHIKITSA-X) — this is an **upgrade, not a rewrite**
**Tagline:** Connected Healthcare for Everyone

---

## 1. One-line positioning

> Jab patient sabse zyada dara hua hota hai, us waqt VedaConnect usse 3 tap mein **sahi hospital + sahi doctor + sahi paisa plan** tak pahuncha deta hai — uski bhasha mein.

We are **not** a hospital directory and **not** an AI doctor. We are a **care navigator**: intake → triage → hospital → booking → in-hospital journey → blood → recovery → feedback.

---

## 2. The 5 real problems (from user research & competitor gap analysis)

| # | Problem | Evidence | Type |
|---|---------|----------|------|
| P1 | Patient in pain/anxiety cannot parse a complex website. Cognitive load peaks exactly when usability matters most. | Practo / Apollo 24\|7 are dense multi-service portals with 40+ nav targets | **Normal problem** (solved badly) |
| P2 | 60%+ of patients think in their mother tongue; health content is English-first. | Only scattered language toggles in Indian health apps | **In-demand problem** |
| P3 | Patient reaches a hospital and finds no bed / wrong specialty / can't afford it. | Repeated OPD→referral→rejection loops | **Unique problem** |
| P4 | Medical reports (lab PDFs, printed slips, photos) are unreadable to patients. | Reports are designed for doctors | **In-demand problem** |
| P5 | Emergency: patient or family member has no idea *which* hospital is 8 minutes away with a trauma ICU + that blood group. | Google Maps gives distance, not capability | **Unique problem** |

**Problem priority rule:** in-demand > unique > normal. We ship in-demand first, unique second, normal last.

---

## 3. Target users

### 3.1 Personas

| Persona | Age | Literacy | Device | Core need |
|---|---|---|---|---|
| **Sunita (patient)** | 34 | Reads Hindi, low English | Android, 4G, 3GB RAM | "Mujhe batao kahan jaana hai, kitna lagega" |
| **Ramesh (elderly patient)** | 67 | Low digital literacy | Shared phone, uses voice | One-button everything, large text |
| **Aarav (caregiver)** | 26 | High | iOS | Manage father's reports, reminders, appointments |
| **Dr. Meera (doctor)** | 41 | High | Desktop in OPD | 30-second patient context, not 20 clicks |
| **Hospital admin** | 38 | Medium | Desktop | Fill beds, reduce no-shows |
| **Blood donor** | 24 | High | Mobile | Find a nearby donation camp in 30 seconds |

### 3.2 Non-users (v1)
- Insurance company claim processors (Phase 9+)
- Pharmacy e-commerce (never — regulated, high liability)
- International patients (Phase 10)

---

## 4. Jobs to be done

1. *"Mere haath mein infection hai — kya hai ye, aur kaunse doctor ko dikhana hai?"*
2. *"Mere paas ₹40,000 hain. Kahan ilaaj ho jayega?"*
3. *"Mere papa ko B+ blood chahiye abhi."*
4. *"Main 2 din se hospital mein hoon — meri dawai kaun de raha hai, kab?"*
5. *"Meri report mein 'Hb 9.1' likha hai — iska matlab kya hai?"*

---

## 5. Feature specification

Legend — **M** = MVP (Phase 1–4), **L** = Later (Phase 5+). Every feature must answer: *which problem does it solve, who pays, is it easy for a sick person.*

### 5.1 Core navigation

| ID | Feature | Problem solved | Monetization | Tag | Acceptance |
|---|---|---|---|---|---|
| F01 | **Calm Mode UI** — one primary action per screen, max 3 choices, 18px+ base font, no nested menus, no carousels | P1 | Retention driver (indirect) | M | A first-time user with no instructions completes "find hospital" in < 60s on a 3GB Android |
| F02 | **Bhashini 22-language switcher** — persistent top-right globe, remembers choice, translates UI + AI output + report explanations, voice input in 12 languages | P2, P4 | Indirect (reach ⇒ bookings) | M | Switching to Tamil changes ≥ 95% of visible strings including error toasts and AI answers |
| F03 | **Emergency Mode** — red pill visible on every screen; one tap → nearest 24×7 trauma-capable facilities ranked by ETA, with call + navigate + blood availability | P5 | Hospital emergency tie-up fee | M | From cold load to a callable emergency hospital ≤ 2 taps |
| F04 | **Hospital finder with exact geo** — Google Places API (New) `Place Details` for canonical `lat/lng`, formatted address, phone; manual pin correction by hospital admin; **Street View "Simulation" preview** so patient recognises the entrance | P3 | Hospital SaaS | M | Displayed pin matches Google place pin; address string identical to `formatted_address` |
| F05 | **Veda Care Score** — transparent 5-vector ranking: clinical fit 35 / affordability 25 / distance 15 / availability 15 / support 10, with "Why recommended?" panel | P3 | Sponsored slots (clearly labelled, never inside Care Score weights) | M | Every recommended hospital exposes its per-vector score breakdown |
| F06 | **AI symptom intake (text + voice)** — structured extraction of symptoms, duration, severity, red flags; outputs **concern level + possible specialty**, never a diagnosis | P1, P4 | Freemium (unlimited after login) | M | Red-flag symptom (chest pain + sweating) always routes to Emergency, overriding AI output |
| F06a | **Image triage** — patient uploads a photo (rash, wound, eye, swelling). Model returns **probability distribution over plausible conditions + confidence + "needs doctor now / can wait" band** | P4 | None directly; drives consultation booking | L | UI never prints a definitive disease name; disclaimer + escalation button always rendered together |
| F07 | **Medical report analyzer** — camera/PDF upload → OCR → plain-language explainer of each parameter with reference range + what to ask the doctor | P4 | Lab/test referral margin | L | Every extracted value editable; low-confidence OCR fields highlighted for confirm |
| F08 | **Care journey tracker** — pre-booking → OPD token → admission → bed allotted → medication given → discharge summary; visible to patient and caregiver | P3 | Hospital SaaS | L | Status changes from hospital dashboard reflect on patient screen ≤ 2s |
| F09 | **Live bed & service availability** — hospital admin edits; shown to patients; expired data auto-marks "unverified 6h ago" | P3 | Hospital SaaS | L | Stale data is never presented as current |
| F10 | **Blood availability + donation** — read-only stock from connected licensed blood banks; donor registration, eligibility quiz, camp discovery, request broadcast | P5 | CSR / grants (never commission on blood) | L | No price, no "sell" flow anywhere; all fulfilment via licensed blood bank |
| F11 | **Medicine reminders** — schedule from prescription OCR or manual, Web Push + WhatsApp, adherence log shared with doctor with consent | P3 | Hospital SaaS | L | Reminder fires within ±2 min of schedule; adherence log is opt-in |
| F12 | **Teleconsultation** — see the same doctor you'd meet offline; 10-min slot; prescription only by registered doctor (Telemedicine Practice Guidelines 2020) | P2 | 15–20% platform fee | L | Session has waiting room, device test, and a generated visit summary |
| F13 | **Results & feedback page** — before/after gallery (consented, anonymised), rating cards with verified-visit badge only | Trust | SEO + conversion | M | Only patients with a confirmed visit ID can post a rating |
| F14 | **Real-time sync** — one source of truth; hospital edits address/beds/rules → patient + doctor dashboards update without refresh | P3 | Hospital SaaS | L | Postgres change → client UI ≤ 2s p95 |
| F15 | **Financial gap engine** (from CHIKITSA-X) — treatment estimate − insurance − PM-JAY − NGO = out-of-pocket | P3 | Lead fee from lenders (disclosed) | M | Formula shown as arithmetic, never a single magic number |
| F16 | **Consent & audit center** — patient sees who accessed what and when; revoke anytime | Trust + DPDP | — | M | Every PHI read writes an immutable audit row with actor, purpose, timestamp |

### 5.2 Dashboard roles
- **Patient / caregiver** — my appointments, reports, reminders, journey, feedback
- **Doctor** — today's queue, patient 360 (symptoms + OCR + triage + prior visits), prescribe, mark journey events
- **Hospital admin** — beds, services, doctors, address/pin, blood stock, emergency capability toggle
- **Super admin** — verification of hospitals, dispute handling, audit viewer

---

## 6. Feature rejection log (features we deliberately do NOT build)

| Rejected | Why |
|---|---|
| **Selling blood** | Buying/selling human blood is prohibited in India; only licensed blood banks may collect and issue. Donation-only via licensed banks. |
| **"Exact disease detection from photo"** | Clinically unsafe and legally indefensible. We ship probabilistic triage + mandatory doctor escalation. |
| **AI-generated prescriptions** | Illegal without a registered practitioner; strictly doctor-issued. |
| **Unverified public doctor reviews** | Defamation + gaming risk; only verified-visit ratings. |
| **Pharmacy checkout in v1** | Drug licensing, cold chain, liability — out of scope. |
| **Insurance claim auto-filing (v1)** | Needs insurer partnerships; keep as estimate + handoff only. |
| **NFT / crypto / gamified streaks** | Looks cool, solves nothing, adds risk. |
| **Chatbot that "answers everything"** | Open-ended medical chat = liability. Only structured intake + scoped Q&A with citations. |
| **Doctor ranking by AI opinion** | We rank **fit**, never quality of a human being. |

---

## 7. Non-functional requirements

| Area | Requirement |
|---|---|
| **Performance** | LCP < 2.5s on 4G / 3GB Android; hospital search < 800ms p95 |
| **Availability** | 99.9% for emergency + hospital search paths |
| **Accessibility** | WCAG 2.2 AA; min touch target 48px; contrast ≥ 4.5:1; full keyboard path |
| **Localisation** | 22 languages, text-expansion safe layouts (+30% width), numerals localisable |
| **Security** | DPDP Act 2023 compliant; OWASP ASVS L2; see rules.md |
| **Offline** | Last-viewed hospital + own appointment cached; emergency numbers always readable offline |
| **Privacy** | No PHI in analytics, logs, or error trackers |

---

## 8. Success metrics

**North star:** *completed care navigations per week* (patient reached a verified care action: booked, called emergency, or consulted).

| Metric | Target (6 months) |
|---|---|
| Median time-to-hospital-decision | < 60s |
| Emergency funnel completion | > 70% |
| Triage → booking conversion | > 25% |
| Language switch usage | > 40% of sessions |
| Verified feedback per 100 bookings | > 12 |
| Hospital SAAS retention | > 80% at 6 months |
| AI escalation-compliance (red flag → emergency) | 100% |

---

## 9. Monetization (in order of activation)

1. **Hospital SaaS** — ₹15k–₹60k/month by bed count (dashboard, bed sync, lead routing, journey tracker). Primary.
2. **Booking / OPD lead fee** — ₹30–₹80 per confirmed token.
3. **Teleconsult fee** — 15–20% of session price.
4. **Lab & diagnostic referral** — disclosed margin.
5. **Sponsored hospital slot** — clearly labelled "Sponsored", capped at 1 per result page, excluded from Care Score.
6. **CSR / grant funding** for the blood-donation module (never commissioned).

Patients never pay for: search, emergency, blood availability, report reading (first 3/month).

---

## 10. Compliance boundaries (non-negotiable)

- Consent before any PHI collection; granular purpose-based consent; easy withdrawal (DPDP Act 2023).
- Registered doctors only for prescriptions; teleconsultation per Telemedicine Practice Guidelines 2020.
- Blood: licensed blood banks only; no consideration/price displayed.
- ABDM/ABHA linking is **opt-in**, never a signup blocker.
- Every AI output carries: *"This is an informational assessment, not a diagnosis"* + one-tap doctor escalation.
