# Planned doc set (outline, working draft)

Owner-reviewed outline of the small documents that will replace the long debate MDs. "Locked" = only the owner may change it (CODEOWNERS + CI check).

- `AGENTS.md` (root, locked, ~150 lines): what RESCA is; system map; folder map with the doc to read first; per-task checklist (before and after); locked files; never list; commands (`make bootstrap/dev/test/check`); definition of done.
- `docs/VISION.md`: problem, users and roles (police, ambulance, fire, civil defence, commander, citizen), the six features, what the demo shows, out of scope.
- `docs/ARCHITECTURE.md` (locked): containers and ownership; communication rules; three end-to-end flows (drone upload to damage map; flood report to electrified-water alert and re-route; offline field report to sync); CPU-only constraints.
- `docs/DECISIONS.md` (locked): one line per decision with reason and rejected alternatives.
- `docs/BACKEND.md`: module layout and layers (router, service, repository); rules with gates (N+1, authorization, transactions and RLS, validation, errors, logging, no raw SQL strings); Ruff, type checker, import-linter, pytest.
- `docs/FRONTEND.md`: web and mobile layout; generated TanStack Query hooks; design tokens as the only style source; Never/Use instead/Exceptions for colours, arbitrary values, inline styles, literal strings, duplicated components, fake data, missing states; role dashboards (widget registry, view presets); mobile specifics; gates.
- `docs/DATABASE.md`: migrations (dbmate, forward only, schema frozen as baseline); RLS and index rules; locked security model; known defects queue; gates.
- `docs/AI.md`: `ai/kaggle/<feature>/vN` layout; shared `ai/src`; weights never in Git; no test-split tuning; promotion with hash and evidence; FastAPI + ONNX serving template and CPU rules; worker contract.
- `docs/DEV_WORKFLOW.md` (locked): Git, contract-first PRs, testing layers, CI and the `ci/ok` check, CODEOWNERS, multi-agent worktree rules.
- `docs/DEPLOY.md`: Contabo + Compose + Caddy, env and SOPS secrets, backups with restore drill, deploy and rollback.
- Folder guides `backend/ frontend/ database/ ai/` AGENTS.md (10-20 lines each) and `docs/documentation/AGENTS.md` for the report.
- `docs/archive/`: the debate, kept, not read by agents.
