# VedaConnect — design.md

Derived from the approved logo (medical cross + ECG pulse + leaf + digital blocks, blue→green gradient) and the "calm for a sick person" requirement.

---

## 1. Brand idea

**Blue = clinical trust. Green = healing & India. Pulse = life. Leaf = care that grows. Pixel blocks = digital.**

The logo already says it: `Veda` (knowledge/blue) + `Connect` (care/green), tagline *"Connected Healthcare for Everyone"* between two heartbeat lines.

---

## 2. Colour tokens

```css
:root {
  /* Brand — sampled from logo */
  --vc-blue-900: #053247;
  --vc-blue-700: #0A5F86;
  --vc-blue-600: #0B6E99;   /* primary brand blue */
  --vc-blue-500: #0E86B8;
  --vc-teal-500: #0FA79B;   /* gradient midpoint of logo */
  --vc-green-600: #17913F;
  --vc-green-500: #1FA24A;  /* primary brand green */
  --vc-green-400: #3CBF63;

  /* Gradient (logo) */
  --vc-grad-brand: linear-gradient(135deg, #0B6E99 0%, #0FA79B 48%, #1FA24A 100%);

  /* Semantic — calm by default */
  --vc-bg: #F7FAFC;          /* page background, soft not pure white */
  --vc-surface: #FFFFFF;
  --vc-surface-alt: #EEF4F8;
  --vc-text: #10232E;        /* 15.1:1 on white */
  --vc-text-muted: #4A6273;  /* 7.0:1 on white */
  --vc-border: #D8E4EC;

  --vc-emergency: #C6271F;   /* red, 5.6:1 on white with white text */
  --vc-emergency-bg: #FDECEA;
  --vc-warning: #B26A00;
  --vc-success: #17913F;
  --vc-info: #0B6E99;

  /* Data viz (colour-blind safe order) */
  --vc-chart-1: #0B6E99;
  --vc-chart-2: #1FA24A;
  --vc-chart-3: #B26A00;
  --vc-chart-4: #6B4FA8;
  --vc-chart-5: #0FA79B;
}
```

**Rules**
- Never use pure black `#000` for text; never pure white page background (glare hurts a patient with a headache).
- Emergency red is reserved exclusively for emergency. No red buttons elsewhere.
- Green is never used for "success toast" alone — always icon + text.
- Dark mode (Phase 10): `--vc-bg: #0C1A21`, surfaces `#132730`, text `#E8F1F5`.

---

## 3. Typography

| Role | Font | Size / line-height |
|---|---|---|
| Display / brand | **Outfit** 600 | 40/44 desktop, 28/32 mobile |
| H1 | Outfit 600 | 32/38 |
| H2 | Outfit 600 | 24/30 |
| H3 | Inter 600 | 20/26 |
| Body | **Inter** 400 | **18/28** (patient-facing), 16/24 (dashboards) |
| Small / meta | Inter 500 | 14/20 |
| Tiny / legal | Inter 400 | 13/18 — **never** below 13px, and never for anything a patient must act on |
| Numerals (data) | Inter tabular | `font-variant-numeric: tabular-nums` |

**Indian language stack (critical):**
```css
font-family: "Inter", "Noto Sans", "Noto Sans Devanagari", "Noto Sans Tamil",
             "Noto Sans Telugu", "Noto Sans Bengali", "Noto Sans Malayalam",
             "Noto Sans Gujarati", "Noto Sans Kannada", "Noto Sans Gurmukhi",
             "Noto Sans Odia", system-ui, sans-serif;
```
Load the Noto script font only for the active locale (dynamic import) to protect LCP on 3GB devices.

**Vernacular sizing:** Devanagari/Tamil/Telugu render ~5–8% smaller at the same px — bump `+1px` body size when `:lang()` is not `en`. Line-height 1.65 minimum for Indic scripts (matras need room).

---

## 4. Spacing, radius, elevation

- 4px base scale: 4, 8, 12, 16, 24, 32, 48, 64.
- Page gutter: 16px mobile, 24px tablet, max-width 1120px desktop with 32px side padding.
- Radius: `8px` inputs/buttons, `14px` cards, `999px` pills, `20px` modals.
- Elevation: only two levels — `0 1px 2px rgba(16,35,46,.06)` (resting card) and `0 12px 32px rgba(16,35,46,.14)` (modal/drawer). No decorative shadows.
- Motion: 150ms ease-out for hovers, 220ms for drawers, 0ms for anything on the Emergency screen. Respect `prefers-reduced-motion`.

---

## 5. Layout language — "One Thing Per Screen"

```
┌─────────────────────────────────────────┐
│ ◆ VedaConnect   [हिंदी ▾]   [🚨 HELP]  │ ← header, sticky, 64px
├─────────────────────────────────────────┤
│                                         │
│   Aapko kya takleef hai?                │ ← H1, one question
│                                         │
│   ┌───────────────────────────────┐     │
│   │  🔍  Bimari ya lakshan likhein │     │ ← primary input, 56px tall
│   └───────────────────────────────┘     │
│                                         │
│   ┌───────────────────────────────┐     │
│   │  🎙  Bolkar bataayein          │     │ ← secondary, same weight
│   └───────────────────────────────┘     │
│                                         │
│   [ Hospital dhoondhein  →  ]           │ ← ONE primary CTA
│                                         │
│   Emergency? Turant madad →             │ ← text link, red
└─────────────────────────────────────────┘
```

**Non-negotiables**
- Max **3** interactive choices visible on a patient screen (excluding header).
- Max **1** filled/primary button per screen; everything else is outline or text.
- No nested navigation deeper than 3 taps to any care action.
- No carousels, no auto-rotating banners, no cookie-style popups (consent is a full page, once).
- Skeleton loaders on `--vc-surface-alt`, never spinners alone.
- Empty states always offer the next action ("No appointments yet → Find a hospital").

---

## 6. Component specs

### Emergency pill
Red `--vc-emergency`, white text, 44px tall, label `🚨 Emergency`, always in header, never scrolls away, `aria-label="Emergency help"`. Tap → `/emergency`. **No confirmation dialog.**

### Hospital card
```
┌──────────────────────────────────────────────┐
│ [thumb]  City Care Hospital      ● Verified  │
│          ★ Care Score 82  ·  3.4 km · 9 min  │
│          Sector 12, Dwarka, New Delhi         │
│          Trauma ICU · 24×7 · B+ available     │
│  [ Call ]            [ Directions ]  [ Why? ] │
└──────────────────────────────────────────────┘
```
- Address wraps, never truncates with `…` (patients need the full address).
- "Why?" opens the Care Score breakdown with 5 labelled bars — no hidden weights.

### Care Score breakdown
Five horizontal bars, each showing `label · weight% · score/100`. Total at top in tabular numerals. Never a single star rating pretending to be quality.

### AI result card (triage / image / report)
```
┌──────────────────────────────────────────────┐
│ ⚠ Informational assessment — not a diagnosis │ ← amber strip, always on top
├──────────────────────────────────────────────┤
│ Possible causes         Confidence: Moderate  │
│  • Fungal infection          61%              │
│  • Contact dermatitis        24%              │
│  • Bacterial infection       15%              │
│                                              │
│ What to do: Doctor within 24–48 hours         │
│                                              │
│ [ Talk to a doctor ]   [ 🚨 Go to emergency ] │
│ Disclaimer v1.2 · Model: … · 02 Nov 2026      │
└──────────────────────────────────────────────┘
```
Disclaimer strip + both CTAs are **one component**. You cannot render the strip without the CTAs (rules A2).

### Language switcher
Globe icon + current language in its own script (`हिंदी`, `தமிழ்`). Opens a sheet listing all 22 with native names, searchable, remembering choice in `localStorage` (locale only, no PHI) and `users.lang`.

### Journey tracker
Vertical stepper: Pre-booked → Checked in → In consult → Admitted → Bed allotted → Medication → Discharged. Current step filled green; timestamps in local time; each step expandable to show actor (hospital/doctor).

### Rating card (feedback page)
Verified-visit badge required. Stars + one-line text + optional before/after images (consent checkbox shown at upload, not buried).

---

## 7. Iconography & imagery

- Icons: `lucide-react`, 1.75px stroke, 20/24px.
- Never use an emoji as the only indicator of meaning (except the emergency pill, which has text too).
- Photography: real Indian hospitals/people, warm daylight, no stock-photo handshakes.
- Illustrations: 2-tone line art in `--vc-blue-600` + `--vc-green-500`.
- The logo mark may be used standalone at ≥ 32px; below that use a solid blue cross glyph.

---

## 8. Accessibility

| Item | Requirement |
|---|---|
| Contrast | ≥ 4.5:1 body, ≥ 3:1 large text and UI borders |
| Touch target | ≥ 48×48px, 8px gap |
| Focus | 2px `--vc-blue-600` ring, `:focus-visible` only |
| Motion | All transitions disabled under `prefers-reduced-motion` |
| Screen reader | `aria-live="polite"` for status/journey updates; `role="alert"` for emergency escalation |
| Forms | Visible labels (never placeholder-only), inline errors tied via `aria-describedby` |
| Language | `<html lang>` switches with locale; `lang` attributes on mixed-language content |
| Elderly mode | Toggle: +2px body, 56px buttons, simplified nav (hides dashboard extras) |

---

## 9. Copy tone

- Address the patient as **"aap"**, short sentences, no medical jargon without a bracketed plain meaning.
- Never say "patient" to the patient — say "aap".
- Numbers always with units and a human comparison: *"9 min door"* not *"3.4 km"* alone.
- Error copy = what happened + what to do next. Never "Something went wrong."
- Emergency copy is imperative and calm: *"Turant madad lein. Nazdeeki emergency hospital: …"*
- AI copy never uses "diagnosis". Approved words: *possible causes, assessment, indicative, consult a doctor*.

---

## 10. Localisation checklist before shipping a screen

1. Longest string test: Tamil + Malayalam at +30% width.
2. Numbers: Devanagari/Tamil numerals optional — keep Latin numerals for clinical values (Hb, BP) to avoid misreading.
3. Time/date: relative ("2 ghante pehle") for < 24h, absolute date after.
4. Currency: `₹1,15,000` with Indian digit grouping, never `1,150,000`.
5. Right-to-left not required for the 22 scheduled languages (all LTR) — skip RTL plumbing.
6. Voice: check ASR accuracy for the top 6 languages before enabling the mic button for a locale.
