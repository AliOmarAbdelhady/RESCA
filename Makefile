# The only task list (docs/DEV_WORKFLOW.md). Same commands for people and agents.
# A gate that is not built yet prints UNRUN; it fails once its folder has code,
# so a missing gate can never look like a pass.

SHELL := /bin/bash
.DEFAULT_GOAL := help
DB_PORT ?= 55432
DB_CONTAINER ?= resca-check-db

.PHONY: help bootstrap check check-policy check-secrets check-static check-db check-api check-ui check-ml

help: ## List the commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-14s %s\n", $$1, $$2}'

bootstrap: ## Install the git hooks (needs uv)
	uvx pre-commit install

check: check-policy check-secrets check-static check-db check-api check-ui check-ml ## Run every gate
	@echo "make check: done (read any UNRUN lines above)"

check-policy: ## Locked paths in the staged change (rule G2)
	python3 tools/policy/check_locked_paths.py --staged

check-secrets: ## Gitleaks on staged changes (rules X4, O3)
	uvx pre-commit run gitleaks --all-files

check-static: ## Ruff lint and format on application Python (rules X1, X6)
	@paths=$$(for p in backend ai tools; do [ -d $$p ] && echo $$p; done); \
	uvx ruff@0.17.6 check $$paths && uvx ruff@0.17.6 format --check $$paths

check-db: ## Build the schema in a throwaway PostGIS 18 and run checks.sql (rules D1-D7)
	docker rm -f $(DB_CONTAINER) >/dev/null 2>&1 || true
	docker run -d --name $(DB_CONTAINER) -e POSTGRES_PASSWORD=check -p $(DB_PORT):5432 \
	  -v $(CURDIR):/repo postgis/postgis:18-3.6 >/dev/null
	docker exec $(DB_CONTAINER) bash -c "apt-get update -qq && apt-get install -y -qq postgresql-18-pgrouting postgresql-18-pgvector >/dev/null"
	docker restart $(DB_CONTAINER) >/dev/null
	until docker exec $(DB_CONTAINER) pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
	docker exec -e PGUSER=postgres -e PGPASSWORD=check -e PGHOST=localhost $(DB_CONTAINER) bash /repo/database/build.sh; \
	  status=$$?; docker rm -f $(DB_CONTAINER) >/dev/null; exit $$status

check-api: ## Backend gates: mypy, import-linter, pytest (rules B1-B14)
	@if [ -f backend/pyproject.toml ]; then \
	  echo "check-api: backend exists but this gate is not built yet (docs/BACKEND.md)"; exit 1; \
	else echo "check-api: UNRUN (no backend yet)"; fi

check-ui: ## Frontend gates: ESLint, types, tests (rules W1-W12, M1-M5)
	@if [ -f frontend/pnpm-lock.yaml ]; then \
	  cd frontend && pnpm install --frozen-lockfile && pnpm run lint && pnpm run typecheck && pnpm run test; \
	elif find frontend/apps frontend/packages -name '*.ts*' | grep -q .; then \
	  echo "check-ui: frontend code exists but pnpm-lock.yaml is missing"; exit 1; \
	else echo "check-ui: UNRUN (no frontend code yet)"; fi

check-ml: ## AI gates: manifests, splits, ONNX parity (rules A1-A6)
	@if [ -d ai/serving ] || [ -d ai/src ]; then \
	  echo "check-ml: AI code exists but this gate is not built yet (docs/AI.md)"; exit 1; \
	else echo "check-ml: UNRUN (no AI service code yet)"; fi
