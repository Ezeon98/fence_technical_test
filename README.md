# Covenant Engine Backend

Deterministic FastAPI backend for facility-specific covenant computation,
hashing, persistence, and blockchain publication.

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

## API

- `POST /api/v1/covenants/compute`
- `GET /api/v1/covenants/{report_id}`
- `GET /health`

## Example request payloads

### Facility Alpha

```json
{
   "facility_id": "facility_alpha",
   "as_of_date": "2026-03-04",
   "portfolio_json": {
      "assets": [
         {
            "id": "A-001",
            "principal": "10000.00",
            "spread_pct": "14.25",
            "days": 180,
            "state": "active"
         },
         {
            "id": "A-002",
            "principal": "9000.00",
            "spread_pct": "11.80",
            "days": 420,
            "state": "active"
         },
         {
            "id": "A-003",
            "principal": "7500.00",
            "spread_pct": "10.50",
            "days": 120,
            "state": "closed"
         }
      ]
   }
}
```

### Facility Beta

```json
{
   "facility_id": "facility_beta",
   "as_of_date": "2026-03-04",
   "portfolio_json": {
      "portfolio": {
         "records": [
            {
               "assetId": "B-001",
               "notional": "25000.00",
               "coupon": "9.70",
               "maturityDays": 90,
               "lifecycle": "performing"
            },
            {
               "assetId": "B-002",
               "notional": "800.00",
               "coupon": "12.20",
               "maturityDays": 120,
               "lifecycle": "performing"
            },
            {
               "assetId": "B-003",
               "notional": "6400.00",
               "coupon": "8.10",
               "maturityDays": 600,
               "lifecycle": "performing"
            }
         ]
      }
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
