# Project Guidelines

## Architecture

- Keep business logic in `src/app/domain` and `src/app/application`; keep IO adapters in `src/app/infrastructure`.
- HTTP entrypoints live in `src/app/api/v1` and should only orchestrate use cases.
- Facility-specific variability must stay isolated per facility folder under `src/app/facilities/<facility_name>/`:
  - `mapper.py`
  - `eligibility.py`
  - `rate_strategy.py`
- Register new facilities only through `src/app/facilities/registry.py`.

## Build And Test

- Recommended local run (full stack):
  - `docker compose up --build`
- After starting containers, deploy contract and set address:
  - `PYTHONPATH=src python scripts/deploy_contract.py`
  - copy deployed address into `.env` as `CONTRACT_ADDRESS`
  - restart API container
- Run all tests:
  - `pytest -q`
- Run integration tests only:
  - `pytest -q tests/integration`

## Conventions

- Use `Decimal` for all financial math; do not use float for rates/amounts.
- Round report rates to two decimals with explicit deterministic behavior.
- Preserve deterministic hashing boundary in `src/app/infrastructure/hash/canonical_hash.py`:
  - do not add DB ids, timestamps, or tx metadata to the canonical payload
  - keep sorted canonical serialization stable
- Use domain ports (`src/app/domain/ports`) for dependency inversion.
- Keep value objects immutable (`@dataclass(frozen=True)` pattern used in domain objects).
- If blockchain publication fails, do not break report computation/persistence flow; preserve graceful degradation.

## Docker And Debugging

- API runs on `8000`; Anvil on `8545`; pgAdmin on `5050`.
- Docker debug attach is opt-in via `.env`:
  - `DEBUG=true`
  - `DEBUG_PORT=3002`
- VS Code attach config is `Python: Attach to API in Docker` (`.vscode/launch.json`).

## Common Pitfalls

- Missing `CONTRACT_ADDRESS` causes smart-contract publication errors.
- Unknown `facility_id` returns 400 from compute endpoint.
- Integration tests require a separate test DB (`TEST_DATABASE_URL`).
- Determinism regressions usually come from unsorted collections or non-Decimal arithmetic.
