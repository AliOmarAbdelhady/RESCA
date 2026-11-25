# Testing

*Draft of the repository's `TESTING.md`. Every claim the product makes has a test that proves it, and every change says which tests prove it. An AI coding agent reads this file before writing any test.*

## 1. The idea in one paragraph

The product makes safety-relevant promises: an agency sees only its incidents, a flood report closes roads in one transaction, a retried message from a phone has no second effect, a model that reaches the server is the model that was evaluated. Each promise has a layer that tests it. Tests run from the fastest to the slowest, and a pull request cannot merge while any required layer fails.

## 2. The layers

| Layer | What it proves | Where | Needs | Runs in |
| --- | --- | --- | --- | --- |
| **Static checks** | Formatting, imports, module boundaries, types, no forbidden imports | All code | Nothing | Seconds |
| **Unit tests** | One function or class does what it says | `backend/tests/unit`, `frontend/**/src/**/*.test.ts`, `ai/libs/**/tests` | Nothing | Seconds |
| **Database tests** | The schema builds from scratch; the self-checks pass; the row-level-security matrix holds; a fresh build equals a migrated database | `database/tests` | PostgreSQL image | About a minute |
| **Integration tests** | The application works against a real PostgreSQL and a real object store | `backend/tests/integration` | PostgreSQL image, object-store image | A few minutes |
| **API contract tests** | Every endpoint honours its OpenAPI document and never answers with a server error | `backend/tests/contract` | The application | A few minutes |
| **Model contract tests** | Each AI service returns the reference output for a tiny input | `ai/services/*/tests`, `ai/libs/serving/tests` | The service with a tiny model | A minute each |
| **AI evaluation gates** | A new model version meets the accuracy, regression, export and latency policy | `ai/training/**` and `ai/registry/policy.yaml` | The CPU runtime | A few minutes |
| **End-to-end tests** | A whole scenario works through the public API, and the console shows it | `scenarios/`, `frontend/**/e2e` | The full stack in Compose | Ten to twenty minutes |
| **Mobile tests** | Mission, SOS and offline sync flows on a device emulator | `frontend/apps/mobile/.maestro` | Emulator | Nightly |
| **Resilience tests** | The console keeps working when AI is unavailable; a retried sync batch has no second effect; a restore from backup works | `scenarios/resilience/`, `deploy/bin/restore.sh` | The full stack, a backup | Nightly |
| **Load check** | The single-user envelope holds with margin | `tools/src/rv_tools/load/` | The full stack | Before a release |
| **Security scans** | No secrets, no known vulnerable dependency, no critical container finding | Whole repository | Scanners | Every pull request |
| **Server benchmark** | Each AI task meets its CPU budget on the real server | `make bench` | The server | After each deployment |

## 3. What a change must prove

| If you change… | These are required |
| --- | --- |
| A function with no I/O | A unit test for the behaviour and for the edge cases |
| SQL, a module's repository, or anything that reads or writes a table | An integration test that runs against the real database |
| `database/schema/` | A migration, the RLS matrix regenerated, the ERD regenerated, and a database test for the new rule |
| An endpoint | The OpenAPI document regenerated, a contract test, and an integration test of the behaviour |
| An event | The event catalogue entry, the schema, and an integration test that the live channel delivers it only to the right audience |
| A model service | The model contract test on the golden fixture, and the OpenAPI snapshot |
| A model version | The version folder complete, and the evaluation gates |
| A contract | The other side regenerated, and its tests |
| The console's behaviour | A component test, plus an end-to-end step if it is part of a scenario |
| The mobile app's behaviour | A component test, and a Maestro flow for anything that involves sync |
| Deployment files | A deployment to staging and its health checks |
| Documentation only | `make docs-check` |

A change that cannot say which tests prove it is not finished.

## 4. The row-level-security matrix

Access control is the most important promise in the product, so it is tested exhaustively rather than by example.

1. A generator reads the database catalog: every table and every policy.
2. For every table, every operation (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) and every demo persona (platform administrator, commander, analyst and responder of the lead agency and of a supporting agency, a user of an agency that has not joined, a citizen), the test executes the operation inside a transaction that is rolled back.
3. It compares the result (allowed, or which error) with the expected matrix kept in `database/tests/rls_expected.yaml`.
4. A new table fails the test until its expected row is written. A changed policy fails until the expectation is changed on purpose, in review.

This is how a mistake that would expose another agency's incident is caught before it is deployed.

## 5. The rule engine, per role

One integration test exists for each way the hazard engine is reached, because the privilege differs:

| Path | Expected |
| --- | --- |
| Analyst reports a hazard and the engine runs | Alert, closures and notifications |
| Worker lands AI-detected hazards and the engine runs | Alert, closures and notifications |
| Field responder reports a hazard | The alert is raised through the agreed privilege path (see the proposal §8.2); the report is kept even if the engine fails |
| Citizen submits a request | No hazard and no alert until the request is verified |
| Commander resolves an alert | Roads reopen unless another live alert covers them |
| The engine runs twice for the same facts | No second alert |

## 6. Scenarios as code

A scenario is a file that describes an incident as a timeline of events: imagery arrives, a flood is reported, a responder moves, a citizen asks for help. The replay tool sends each event through the **public API** at the time the file asks for and then checks the expectations.

- **For tests.** `scenarios/<name>/expected.yaml` states what must be true at the end: which alert exists, how many segments are closed, who was notified, which routes are invalid.
- **For resilience.** A scenario can include faults: "stop the damage service", "cut the connection for two minutes". The expectations then describe what must keep working.
- **For the demonstration.** The same file replays the recorded incident. Nothing is typed by hand in front of an audience.
- **For evaluation.** A scenario measures the alert-path latency and records it with the release.

Scenarios contain no personal data.

## 7. Fixtures and tiny models

The whole pipeline must be testable on a CPU-only runner in minutes. So:

- `fixtures/rasters/` holds tiny georeferenced images with known content.
- `fixtures/network/` holds a miniature road network for routing tests.
- `fixtures/models/` holds a tiny model for each AI task with the same input and output contract as the real one. It is too weak to use and exactly right for testing.

Real models are exercised by the evaluation gates, on the data and hardware where that is meaningful.

## 8. Speed rules

- The pull-request pipeline finishes in about fifteen minutes. Anything longer runs nightly or before a release.
- Tests that need PostgreSQL start it once and create a database from a template for each test class.
- Tests never depend on order and never share a database.
- A test that fails without a code change is a bug in the test and is fixed in the same week.
- Coverage is watched, not chased. The rule is in §3: each change proves itself.

## 9. Rules for AI coding agents

- Write the test first when the behaviour is small and clear; otherwise write it with the code. Never leave it for later.
- Never weaken, skip or delete a test to make a change pass. If a test is wrong, change it and explain why in the pull request.
- Never mock the database in an integration test. Use the real one.
- Never test only the happy path for anything that touches permissions, money, routing or alerts.
- Never commit a test that needs a GPU, a network service or a real credential.
- Run `make check` before opening a pull request and paste nothing: CI runs the same command.

## 10. Commands

```bash
make test-fast         # static checks and unit tests, everything
make test-db           # database build, self-checks, RLS matrix
make test-integration  # backend against real PostgreSQL and object storage
make test-contract     # API, model and event contracts
make test-ai           # model contract tests and evaluation gates
make test-e2e          # one scenario through the full stack
make test              # everything that runs on a pull request
make check             # test plus docs and repository checks; what CI requires
make bench             # CPU latency on this machine; run it on the server
```
