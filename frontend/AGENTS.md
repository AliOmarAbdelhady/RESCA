# frontend/AGENTS.md

Web console (`apps/web`), Expo app (`apps/mobile`), shared packages. Read [docs/FRONTEND.md](../docs/FRONTEND.md) before any change. Locked.

Gate: `make check-ui` with zero warnings.

Most-broken rules here:
1. Hex, rgb or named colours, default palette classes, `[arbitrary]` values or inline styles. Use the tokens in `packages/config/tailwind/theme.css` (W1).
2. English text in a component. Use `t()` and add `en` and `ar` keys together; check the screen in Arabic (W3).
3. A copied component. Extend the shared one in `packages/ui` with a variant (W2).
4. `fetch`, `axios` or mock data in a screen. Use the generated hooks in `packages/api` and handle loading, empty, error and denied states (W4).
5. `ml-`/`mr-`/`pl-`/`pr-`. Use `ms-`/`me-`/`ps-`/`pe-` so RTL mirrors (W3).
6. An empty `catch` or a promise nobody awaits (X1).
7. Hiding a widget as if it were security. The server authorizes every call (W12).
