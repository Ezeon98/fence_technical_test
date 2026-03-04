# Covenant Engine Backend

Deterministic FastAPI backend for facility-specific covenant computation,
hashing, persistence, and blockchain publication.

## Requirements

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 16 (local or dockerized)

## Architecture highlights

- Explicit normalization boundary through `NormalizedAsset`.
- Facility mappers under `src/app/facilities/{facility_name}/mapper.py`.
- Deterministic covenant hash with canonical JSON + SHA-256.
- Database persistence of full reports and report hash.
- Smart-contract publication of immutable covenant evidence.
- Graceful degradation when blockchain publication fails.

## Deterministic hash boundary

The report hash includes only:

- `facility_id`
- `as_of_date`
- `effective_rate` (two-decimal string)
- `covenant_status`
- `included_asset_ids` (sorted)
- `excluded_assets_with_reasons` (sorted)

The hash excludes:

- Database identifiers
- Blockchain transaction hash
- Persistence timestamps

## On-chain rate representation

- Rates are computed with `Decimal` only.
- Rounded to two decimals for report output.
- Converted to integer basis points for chain storage.
  - Example: `18.54% -> 1854 bps`

## Docker services

- `api`: FastAPI backend
- `postgres`: full report persistence
- `anvil`: local EVM chain

## Setup

1. Copy `.env.example` to `.env`.
2. Start services:
   - `docker-compose up --build`
3. Deploy the contract to Anvil:
   - `PYTHONPATH=src python scripts/deploy_contract.py`
4. Put deployed address into `.env` as `CONTRACT_ADDRESS`.
5. Restart API service.

## Configuration

Main environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection used by the API.
- `TEST_DATABASE_URL`: Optional override used by integration tests.
- `RPC_URL`, `CHAIN_ID`, `DEPLOYER_PRIVATE_KEY`, `CONTRACT_ADDRESS`:
   Smart-contract publishing settings.

## API

- `POST /api/v1/covenants/compute`
- `GET /api/v1/covenants/{report_id}`
- `GET /health`

## Testing and CI

Run all tests locally:

```bash
pytest -q
```

Run integration tests only:

```bash
pytest -q tests/integration
```

Run integration tests against dockerized PostgreSQL:

```bash
docker compose run --rm \
   -e TEST_DATABASE_URL=postgresql://postgres:postgres@postgres:5432/covenants_test \
   api pytest -q tests/integration
```

Integration tests in `tests/integration/test_covenant_flow.py` validate:

- End-to-end covenant flow for `facility_educa`, `facility_payearly`, and
   `facility_nomina`.
- Deterministic outputs: `effective_rate`, `covenant_status`,
   `included_asset_ids`, `excluded_assets_with_reasons`, and `report_hash`.
- Real database behavior with `PostgresReportRepository`, including
   `ON CONFLICT` idempotency, unique `report_hash`, JSONB persistence, and
   transaction commit behavior.

## Example request payloads

### Facility Educa (Educa Capital I)

```json
{
   "facility_id": "facility_educa",
   "as_of_date": "2026-03-04",
   "portfolio_json": {
      "assets": [
         {
            "external_id": "EDU-001",
            "status": "open",
            "is_eligible": true,
            "outstanding_amount": "10000.00",
            "interest_rate_percentage": "18.50",
            "loan_status": "current"
         },
         {
            "external_id": "EDU-002",
            "status": "open",
            "is_eligible": true,
            "outstanding_amount": "8300.00",
            "interest_rate_percentage": null,
            "loan_status": "current"
         },
         {
            "external_id": "EDU-003",
            "status": "closed",
            "is_eligible": true,
            "outstanding_amount": "5000.00",
            "interest_rate_percentage": "15.20",
            "loan_status": "current"
         }
      ]
   }
}
```

### Facility PayEarly (PayEarly US)

```json
{
   "facility_id": "facility_payearly",
   "as_of_date": "2026-03-04",
   "portfolio_json": {
      "assets": [
         {
            "external_id": "PAY-001",
            "status": "performing",
            "is_eligible": true,
            "outstanding_principal_amount": "2000.00",
            "total_principal_amount": "2500.00",
            "total_fee_amount": "75.00",
            "created_at": "2026-01-10T00:00:00Z",
            "due_date": "2026-02-10"
         },
         {
            "external_id": "PAY-002",
            "status": "performing",
            "is_eligible": false,
            "outstanding_principal_amount": "1100.00",
            "total_principal_amount": "1300.00",
            "total_fee_amount": "39.00",
            "created_at": "2026-01-05T00:00:00Z",
            "due_date": "2026-01-20"
         },
         {
            "external_id": "PAY-003",
            "status": "performing",
            "is_eligible": true,
            "outstanding_principal_amount": "0.00",
            "total_principal_amount": "900.00",
            "total_fee_amount": "18.00",
            "created_at": "2026-01-15T00:00:00Z",
            "due_date": "2026-01-30"
         }
      ]
   }
}
```

### Facility Nomina (Nomina Express I)

```json
{
   "facility_id": "facility_nomina",
   "as_of_date": "2026-03-04",
   "portfolio_json": {
      "assets": [
         {
            "external_id": "NOM-001",
            "status": "active",
            "is_eligible": true,
            "outstanding_amount": "4500.00",
            "fee_percentage": "0.12",
            "origination_date": "2026-01-01",
            "maturity_date": "01/04/2026"
         },
         {
            "external_id": "NOM-002",
            "status": "active",
            "is_eligible": false,
            "outstanding_amount": "2200.00",
            "fee_percentage": "0.10",
            "origination_date": "2026-01-15",
            "maturity_date": "15/03/2026"
         },
         {
            "external_id": "NOM-003",
            "status": "inactive",
            "is_eligible": true,
            "outstanding_amount": "3100.00",
            "fee_percentage": "0.11",
            "origination_date": "2026-02-01",
            "maturity_date": "01/05/2026"
         }
      ]
   }
}
```

## Architectural rationale

- **Why Clean Architecture**: It keeps deterministic covenant logic inside
   domain/application layers and isolates IO concerns (DB, chain, HTTP) in
   infrastructure adapters. This improves testability and reduces coupling.
- **How facility variability is isolated**: Each facility owns its mapper,
   eligibility, and rate strategy under `src/app/facilities/*`, while the core
   use case depends only on stable ports and normalized value objects.
- **Why canonical hashing is necessary**: Independent verifiers need the same
   dataset to produce the exact same hash. Canonical ordering and stable string
   formatting remove ambiguity from serialization.
- **DB-only vs blockchain trade-offs**: DB-only is simpler, cheaper, and easier
   to query for full reports. Blockchain publishing adds tamper-evident
   attestation and shared trust, but increases operational complexity,
   dependencies, and transaction latency/cost.

## Production evolution

- **Migration handling (Alembic)**: Introduce Alembic revision workflows for
   controlled schema changes and repeatable environment upgrades.
- **Access control for smart contract**: Add role-based permissions (for
   example `Ownable`/`AccessControl`) so only authorized publishers can write.
- **Observability and metrics**: Add structured logs, request tracing, and
   metrics for compute duration, publish success rate, and chain confirmation
   latency.
- **Retry strategy for blockchain publishing**: Add idempotent retry workers
   with bounded exponential backoff, dead-letter handling, and reconciliation
   jobs for failed on-chain submissions.
