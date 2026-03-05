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

## Docker debug attach (VS Code)

Run the API with remote debug enabled by setting these variables in `.env`:

- `DEBUG=true`
- `DEBUG_PORT=3002` (optional, default `3002`)

Then start the stack:

```bash
docker compose up --build
```

In VS Code, run the `Python: Attach to API in Docker` launch config to attach
the debugger to the running `api` container.

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


## How the covenant model shaped the architecture

A covenant is not simply a computed metric — it is a contractual obligation
between two parties (Capital Provider and Asset Originator) who do not share
a single trusted system. Once published, the rate must be:

- **Independently verifiable**: either party must be able to reproduce the
  exact same value from the same inputs, without relying on Fence as
  intermediary.
- **Tamper-evident**: no party, including Fence itself, should be able to
  silently alter a published result after the fact.
- **Consequential**: the rate can automatically trigger downstream actions
  (disbursement pauses, cap reviews, waterfall adjustments), so correctness
  and finality are non-negotiable.

These three properties drove the following concrete decisions:

**Canonical hashing over raw persistence.** Storing the full report in a
database is not sufficient for a covenant. A database record can be updated
or deleted. The SHA-256 hash over a deterministically ordered subset of the
report (facility, date, rate, status, asset lists) means any party can
recompute the hash independently and detect any tampering. The hash is
the covenant fingerprint.

**Blockchain publication as shared trust anchor.** Publishing the hash
on-chain removes the need for either party to trust Fence's database. The
smart contract is neutral ground: neither the Capital Provider nor the Asset
Originator controls it, and the transaction hash provides an immutable
timestamp. This is why blockchain publication is treated as a first-class
output, not a nice-to-have.

## Reasoning and assumptions

**Status normalization is case-insensitive.**
The sample data contains inconsistent casing for the same logical value
(`"open"`, `"Open"`, `"OPEN"`). All mappers normalize status to lowercase
before applying eligibility rules, treating these as equivalent. This is
assumed to be a data quality issue on the originator side, not intentional
differentiation.

**`as_of_date` is metadata, not a filter.**
The challenge does not specify that assets should be filtered by date. The
`as_of_date` field is included in the covenant report and its hash as a
reference timestamp — it documents *when* the computation was run, but does
not exclude assets whose `effective_date` or `origination_date` falls after
it. If date-based filtering were required, it would need to be defined
per-facility in the Credit Agreement.

**`is_eligible` is treated as an explicit override.**
Even if an asset passes all other eligibility criteria, `is_eligible: false`
always excludes it. This flag is assumed to represent a manual or upstream
system override that takes precedence over formula-based rules.

**Repayment months uses whole calendar months.**
For Facility C, `repayment_months` is computed as the difference in calendar
months between `origination_date` and `maturity_date`, without rounding or
day-level adjustment. This matches the formula in the Credit Agreement and
avoids introducing precision that the agreement does not define.

**Tenor days for Facility B uses calendar days.**
`tenor_days` is the raw difference in days between `created_at` and
`due_date`. No business-day calendar or holiday adjustment is applied, as
none is specified in the Credit Agreement.

**Assets with zero denominator are excluded gracefully.**
If all eligible assets have zero outstanding principal (or outstanding
amount), the effective rate returns `0.00` rather than raising an error.
This prevents a single bad portfolio snapshot from crashing the computation
pipeline.

**The smart contract stores only the hash, not the full report.**
Storing the full report on-chain would be cost-prohibitive and unnecessary.
The hash is sufficient for independent verification: any party with the
original report data can recompute the hash and compare it against the
on-chain record. The full report is persisted in PostgreSQL for operational
queries and audits.

**Blockchain publication uses a local Anvil chain for this implementation.**
A production deployment would target a public or permissioned EVM-compatible
network. The publisher interface is network-agnostic — swapping the RPC URL
and contract address is sufficient to target any chain.