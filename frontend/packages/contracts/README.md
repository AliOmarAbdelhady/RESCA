# packages/contracts — shared domain language

Pure TypeScript: types, enums, constants, zod schemas. **No I/O, no platform APIs,
no imports from apps or other packages** (except nothing — this is the bottom of the
stack alongside `utils`).

Every surface reads the same definitions from here — web charts, mobile map legends,
urgency badges, role guards — so the product speaks one vocabulary everywhere.

```
src/
  damage.ts      # DAMAGE_CLASSES: id, i18n label key, severity token name (no colour values, W1)
  urgency.ts     # urgency levels + thresholds
  geo.ts         # GeoJSON feature types, coordinate helpers, distance units
  user.ts        # roles (COMMANDER / ANALYST / FIELD_RESPONDER / AGENCY_ADMIN) + permissions matrix
  events.ts      # zod schemas for every SSE event envelope (C2): position, sos,
                 #   job-progress, victim; validated at the stream boundary
```

## Rules

- If two surfaces would otherwise redefine the same domain concept, the concept
  belongs here.
- Adding an event type = add zod schema + regenerate nothing else; both apps get
  compile-time knowledge of it through `@resca/api/realtime`.
