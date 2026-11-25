# Frontend

One pnpm + Turborepo workspace in `frontend/`: the web console, the Expo field app and shared packages. Most frontend bugs are hard-coded colours, styles, strings and copied components; the lint config makes each of those a build error.

## Layout

```
frontend/
  apps/web/            Vite + React + TanStack Router (static build served by Caddy)
    src/routes/        file-based routes; pages compose widgets and shared components
    src/features/<f>/  feature widgets, hooks and view logic (no raw API calls)
  apps/mobile/         Expo Router app, development builds only
    src/features/<f>/  same idea as web
    src/services/      native adapters: location, storage, camera, background tasks
  packages/api/        generated OpenAPI client + TanStack Query hooks + SSE client (the only way to call the backend)
  packages/contracts/  shared enums and event schemas (Zod), generated where possible
  packages/ui/         shared components: shadcn/ui wrappers for web, React Native Reusables for mobile
  packages/i18n/       en.json and ar.json, the only place user-visible text lives
  packages/config/     eslint, tsconfig, Tailwind theme (tokens). Locked.
```

Pinned lint toolchain (tested 25 November 2026): `eslint@9.39.5`, `typescript@6.0.3`, `typescript-eslint@8.74.0`, `eslint-plugin-better-tailwindcss@4.11.0`, `eslint-plugin-i18next@6.1.5`, `eslint-plugin-react-native@5.0.0`, `eslint-plugin-react-hooks@7.1.1`, `tailwindcss@4.3.5`. eslint-plugin-react-native does not support ESLint 10 and typescript-eslint does not support TypeScript 7 yet; upgrade only together, through the owner.

## Design tokens (W1)

`packages/config/tailwind/theme.css` is the only file that contains colour, font, radius or shadow values. It switches off Tailwind's default palette, so classes like `bg-red-500` do not exist.

| Never | Use instead |
|---|---|
| `#ff0000`, `rgb()`, `hsl()`, `'red'` anywhere in code | a token class: `bg-surface`, `text-fg-muted`, `border-border` |
| `bg-red-500`, any default palette class | `bg-severity-critical`, `text-accent`, `bg-agency` |
| `p-[13px]`, `text-[#fff]`, any `[...]` value | the nearest scale step, or ask the owner to add a token |
| `style={{ ... }}` on web, inline styles on mobile | token classes or a component variant |
| `ml-4`, `pr-2`, `left-0` | `ms-4`, `pe-2`, `start-0` (mirrors for Arabic) |
| building class names from strings (`"bg-" + c`) | a variant map in the component (`cva`) |

Severity colours (critical, high, moderate, low, info) mean the same thing for every agency and role. Agency accents use only hues that are not severity colours and appear only in chrome, never on data a responder acts on. Exceptions, each with a comment: map style JSON for MapLibre (generated from tokens at build time), brand artwork and flag glyphs.

## Rules

| ID | Rule | Gate |
|---|---|---|
| X1 | Never swallow an error: no empty `catch`, no promise left unhandled, throw only `Error` objects. | `no-empty`, `@typescript-eslint/no-floating-promises`, `no-misused-promises`, `only-throw-error` |
| W1 | Tokens only (table above). | `better-tailwindcss/no-unknown-classes`, `no-restricted-classes`, `enforce-logical-properties`, `no-concatenated-classes`, colour-literal and inline-style bans |
| W2 | Reuse before you build. Pages compose shared components from `packages/ui` and feature widgets; apps never import Radix or other primitives directly. Wrap a primitive once and expose variants; do not copy a component to change it. | `no-restricted-imports`; review for near-duplicates |
| W3 | **No user-visible text in code.** Every string, label, placeholder, `aria-label`, toast and error goes through `t()`. Add English and Arabic keys together with the same placeholders. Numbers and dates use locale formatting. Test every new screen in Arabic (RTL). | `i18next/no-literal-string`; key-parity check; RTL browser test |
| W4 | Data comes only from the generated client and hooks in `packages/api`. Every data view handles loading, empty, denied, stale, error and success from real responses. No fake data in screens. Clear cached queries when the user changes. | `fetch`/`axios`/mock imports banned in apps; browser tests per state |
| W5 | Forms use TanStack Form + Zod; server field errors map to fields; input is kept on error; double submit is impossible. The server validates again. | Browser tests |
| W6 | Shareable state (filters, selection, map view) lives in validated TanStack Router search params; server data in TanStack Query; short-lived UI state in Zustand. Nothing sensitive in URLs. | Lint on store imports; browser tests |
| W7 | One MapLibre instance per visible map; viewport-bounded queries; stable deck.gl layer IDs; positions updated incrementally, never by re-mounting. | Replay 1,000 points at 10 updates/s; p95 frame under 50 ms |
| W8 | WCAG 2.2 AA on operational screens: keyboard, focus, contrast, never colour alone (add icon or text), a list alternative to every map-only action. | axe in Playwright; keyboard tests |
| W9 | Initial JavaScript for the dispatch shell at most 250 KiB gzip; maps and analytics load lazily. Targets: LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1. | Bundle and trace checks |
| W10 | Error boundaries per route and per widget, with a translated recovery action and a visible "last updated" time. A broken widget never blanks the dashboard or hides SOS. | Injected-failure tests |
| W11 | No tokens in localStorage or sessionStorage: Secure, HttpOnly, SameSite session cookies with CSRF protection on writes. Render untrusted text as text; no `dangerouslySetInnerHTML`. Strict CSP. | Lint ban; edge tests |
| W12 | Role dashboards come from typed view presets (agency × role) and a widget registry. Users cannot rearrange. Hiding a widget is presentation only: the server still authorizes every call. | Preset validation; direct-API denial tests |

## Role dashboards

A page such as `/incidents/$incidentId` does not hard-code its panels. It loads the preset for the user's agency (`government`, `police`, `ems`, `fire`) and role (`COMMANDER`, `ANALYST`, `FIELD_RESPONDER`, `AGENCY_ADMIN`), sets `data-agency` on the shell for the accent, and renders the listed widgets in their grid positions. Each widget declares the permission it needs and is skipped if the user lacks it.

## Mobile (Expo)

| ID | Rule | Gate |
|---|---|---|
| M1 | Development builds only (never Expo Go). Same tokens and translations through NativeWind and React Native Reusables; native accessibility labels on every control; test in Arabic with large text. | `react-native/no-color-literals`, `no-inline-styles`, `no-raw-text`, `no-unused-styles` |
| M2 | Commands made offline are saved in SQLite with user, incident, idempotency key, payload version, expiry and retry state. **A queued SOS stays visibly "not sent" until the server confirms it.** | Kill-and-restart tests between save, send and confirm |
| M3 | Ask for location permission in context; track in the background only during a visible, authorized shift; stop on logout or revoke; show the age and accuracy of the last fix. | Permission and revoke tests |
| M4 | Session secrets in SecureStore; offline data separated per user and deleted on sign-out. | Account-switch tests |
| M5 | Batch GPS, limit cache and queue size, virtualize long lists, strip personal data from crash reports. | 30-minute shift test on a real device before release |

## Definition of done for a frontend change

- `make check-ui` passes with zero warnings; no `eslint-disable` added.
- New screen: English and Arabic keys, RTL checked, all data states handled, keyboard reachable.
- New component: lives in `packages/ui` if two features could use it; has variants instead of copies.
- API change: generated client regenerated from the merged contract (C1), never edited by hand.
