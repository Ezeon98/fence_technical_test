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
         "external_id": "EDU-STU-10001",
         "effective_date": "2024-06-25",
         "reporting_date": "2026-01-15",
         "status": "open",
         "is_eligible": true,
         "student_id": "STU-10001",
         "school_id": "SCH-001",
         "loan_status": "current",
         "disbursement_amount": 6500.00,
         "outstanding_amount": 4875.00,
         "repaid_amount": 1625.00,
         "interest_rate_percentage": 20.86,
         "days_past_due": 0,
         "country": "ES",
         "amount": 6500.00
         },
         {
         "external_id": "EDU-STU-10002",
         "effective_date": "2024-08-15",
         "reporting_date": "2026-01-15",
         "status": "open",
         "is_eligible": true,
         "student_id": "STU-10002",
         "school_id": "SCH-002",
         "loan_status": "current",
         "disbursement_amount": 12000.00,
         "outstanding_amount": 10200.00,
         "repaid_amount": 1800.00,
         "interest_rate_percentage": 18.54,
         "days_past_due": 0,
         "country": "ES",
         "amount": 12000.00
         },
         {
         "external_id": "EDU-STU-10003",
         "effective_date": "2024-05-10",
         "reporting_date": "2026-01-15",
         "status": "open",
         "is_eligible": false,
         "student_id": "STU-10003",
         "school_id": "SCH-001",
         "loan_status": "delinquent",
         "disbursement_amount": 7850.00,
         "outstanding_amount": 7100.00,
         "repaid_amount": 750.00,
         "interest_rate_percentage": 25.11,
         "days_past_due": 90,
         "country": "ES",
         "amount": 7850.00
         },
         {
         "external_id": "EDU-STU-10004",
         "effective_date": "2024-09-01",
         "reporting_date": "2026-01-15",
         "status": "open",
         "is_eligible": true,
         "student_id": "STU-10004",
         "school_id": "SCH-003",
         "loan_status": "current",
         "disbursement_amount": 15000.00,
         "outstanding_amount": 14250.00,
         "repaid_amount": 750.00,
         "interest_rate_percentage": 16.20,
         "days_past_due": 0,
         "country": "ES",
         "amount": 15000.00
         },
         {
         "external_id": "EDU-STU-10005",
         "effective_date": "2024-03-20",
         "reporting_date": "2026-01-15",
         "status": "Open",
         "is_eligible": true,
         "student_id": "STU-10005",
         "school_id": "SCH-002",
         "loan_status": "current",
         "disbursement_amount": 9500.00,
         "outstanding_amount": 6650.00,
         "repaid_amount": 2850.00,
         "interest_rate_percentage": 22.00,
         "days_past_due": 0,
         "country": "ES",
         "amount": 9500.00
         },
         {
         "external_id": "EDU-STU-10006",
         "effective_date": "2024-07-12",
         "reporting_date": "2026-01-15",
         "status": "closed",
         "is_eligible": false,
         "student_id": "STU-10006",
         "school_id": "SCH-001",
         "loan_status": "written_off",
         "disbursement_amount": 3200.00,
         "outstanding_amount": 3200.00,
         "repaid_amount": 0.00,
         "interest_rate_percentage": 19.50,
         "days_past_due": 180,
         "country": "ES",
         "amount": 3200.00
         },
         {
         "external_id": "EDU-STU-10007",
         "effective_date": "2024-11-05",
         "reporting_date": "2026-01-15",
         "status": "OPEN",
         "is_eligible": true,
         "student_id": "STU-10007",
         "school_id": "SCH-003",
         "loan_status": "current",
         "disbursement_amount": 18000.00,
         "outstanding_amount": 16200.00,
         "repaid_amount": 1800.00,
         "interest_rate_percentage": 17.80,
         "days_past_due": 0,
         "country": "ES",
         "amount": 18000.00
         },
         {
         "external_id": "EDU-STU-10008",
         "effective_date": "2025-01-20",
         "reporting_date": "2026-01-15",
         "status": "open",
         "is_eligible": true,
         "student_id": "STU-10008",
         "school_id": "SCH-001",
         "loan_status": "current",
         "disbursement_amount": 7000.00,
         "outstanding_amount": 7000.00,
         "repaid_amount": 0.00,
         "interest_rate_percentage": null,
         "days_past_due": 0,
         "country": "ES",
         "amount": 7000.00
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
         "external_id": "a49c66dd-507d-4087-8ba7-be54153040ef",
         "created_at": "2023-07-22T13:52:25+00:00",
         "due_date": "2025-07-28",
         "last_updated": "2026-01-20T17:23:11.783Z",
         "status": "defaulted",
         "is_eligible": false,
         "employer_id": "1d369e20-0e9a-410f-98cb-e4977a0a0240",
         "employer_name": "ClearHaven Hospitality Group",
         "employee_id": "0f2af6bd-3da3-11ed-91b9-0242ac110011",
         "user_state": "WI",
         "total_principal_amount": 7111.86,
         "outstanding_principal_amount": 7111.86,
         "repaid_principal_amount": 0.00,
         "total_fee_amount": 2.92,
         "outstanding_fee_amount": 2.92,
         "receivable_currency": "USD",
         "days_past_due": 199,
         "amount": 7111.86
         },
         {
         "external_id": "b60d823e-618e-4f08-9c98-cf65264151f0",
         "created_at": "2025-06-15T09:00:00+00:00",
         "due_date": "2026-03-15",
         "last_updated": "2026-01-20T17:23:11.783Z",
         "status": "PERFORMING",
         "is_eligible": true,
         "employer_id": "1d369e20-0e9a-410f-98cb-e4977a0a0240",
         "employer_name": "ClearHaven Hospitality Group",
         "employee_id": "ac40b215-74ca-5d6b-a2de-519f464663d9",
         "user_state": "WI",
         "total_principal_amount": 8500.00,
         "outstanding_principal_amount": 3400.00,
         "repaid_principal_amount": 5100.00,
         "total_fee_amount": 1.75,
         "outstanding_fee_amount": 1.75,
         "receivable_currency": "USD",
         "days_past_due": 0,
         "amount": 8500.00
         },
         {
         "external_id": "c71e934f-729f-5a19-ad09-da76375262a1",
         "created_at": "2025-08-01T14:30:00+00:00",
         "due_date": "2026-06-01",
         "last_updated": "2026-01-20T17:23:11.783Z",
         "status": "performing",
         "is_eligible": true,
         "employer_id": "1d369e20-0e9a-410f-98cb-e4977a0a0240",
         "employer_name": "ClearHaven Hospitality Group",
         "employee_id": "c76895c9-7553-541c-b19f-09d9dd5ff662",
         "user_state": "TX",
         "total_principal_amount": 22300.50,
         "outstanding_principal_amount": 15610.35,
         "repaid_principal_amount": 6690.15,
         "total_fee_amount": 4.60,
         "outstanding_fee_amount": 4.60,
         "receivable_currency": "USD",
         "days_past_due": 0,
         "amount": 22300.50
         },
         {
         "external_id": "d82fa45a-830a-6b20-be10-eb87486373b2",
         "created_at": "2025-09-10T08:00:00+00:00",
         "due_date": "2026-02-28",
         "last_updated": "2026-01-20T17:23:11.783Z",
         "status": "performing",
         "is_eligible": true,
         "employer_id": "2e470f31-1fab-521a-a9dc-f5088b1b1351",
         "employer_name": "Summit Ridge Healthcare",
         "employee_id": "6f393afe-61b5-5e40-88fc-a427b0ce0346",
         "user_state": "CA",
         "total_principal_amount": 5200.00,
         "outstanding_principal_amount": 2600.00,
         "repaid_principal_amount": 2600.00,
         "total_fee_amount": 1.10,
         "outstanding_fee_amount": 1.10,
         "receivable_currency": "USD",
         "days_past_due": 0,
         "amount": 5200.00
         },
         {
         "external_id": "e93ab56b-941b-7c31-cf21-fc98597484c3",
         "created_at": "2025-10-01T11:00:00+00:00",
         "due_date": "2026-01-15",
         "last_updated": "2026-01-20T17:23:11.783Z",
         "status": "delinquent",
         "is_eligible": true,
         "employer_id": "2e470f31-1fab-521a-a9dc-f5088b1b1351",
         "employer_name": "Summit Ridge Healthcare",
         "employee_id": "48bce6fd-cdb1-58d4-a534-a2c3e43042a7",
         "user_state": "CA",
         "total_principal_amount": 31000.00,
         "outstanding_principal_amount": 28500.00,
         "repaid_principal_amount": 2500.00,
         "total_fee_amount": 6.40,
         "outstanding_fee_amount": 6.40,
         "receivable_currency": "USD",
         "days_past_due": 45,
         "amount": 31000.00
         },
         {
         "external_id": "f04bc67c-a52c-8d42-da32-ad09608595d4",
         "created_at": "2025-11-15T10:00:00+00:00",
         "due_date": "2026-05-10",
         "last_updated": "2026-01-20T17:23:11.783Z",
         "status": "performing",
         "is_eligible": true,
         "employer_id": "3f581a42-2abc-632b-bae0-a6199c2c2462",
         "employer_name": "Beacon Valley Logistics",
         "employee_id": "48f5f800-6b30-5a90-a891-32673943f403",
         "user_state": "FL",
         "total_principal_amount": 18750.00,
         "outstanding_principal_amount": 12500.00,
         "repaid_principal_amount": 6250.00,
         "total_fee_amount": 3.85,
         "outstanding_fee_amount": 3.85,
         "receivable_currency": "USD",
         "days_past_due": 0,
         "amount": 18750.00
         },
         {
         "external_id": "g15cd78d-b63d-9e53-eb43-be10719606e5",
         "created_at": "2025-12-01T09:30:00+00:00",
         "due_date": "2026-08-01",
         "last_updated": "2026-01-20T17:23:11.783Z",
         "status": "Performing",
         "is_eligible": true,
         "employer_id": "3f581a42-2abc-632b-bae0-a6199c2c2462",
         "employer_name": "Beacon Valley Logistics",
         "employee_id": "7b3878bc-bf83-5f2e-b4f4-3bf170646a17",
         "user_state": "FL",
         "total_principal_amount": 42000.00,
         "outstanding_principal_amount": 33600.00,
         "repaid_principal_amount": 8400.00,
         "total_fee_amount": 8.65,
         "outstanding_fee_amount": 8.65,
         "receivable_currency": "USD",
         "days_past_due": 0,
         "amount": 42000.00
         },
         {
         "external_id": "h26de89e-c74e-0f64-fc54-cf21820717f6",
         "created_at": "2025-05-01T08:00:00+00:00",
         "due_date": "2025-12-31",
         "last_updated": "2026-01-20T17:23:11.783Z",
         "status": "repaid",
         "is_eligible": true,
         "employer_id": "1d369e20-0e9a-410f-98cb-e4977a0a0240",
         "employer_name": "ClearHaven Hospitality Group",
         "employee_id": "2a3eb441-2acd-5218-877f-c55fd4d78455",
         "user_state": "WI",
         "total_principal_amount": 950.00,
         "outstanding_principal_amount": 0.00,
         "repaid_principal_amount": 950.00,
         "total_fee_amount": 0.20,
         "outstanding_fee_amount": 0.00,
         "receivable_currency": "USD",
         "days_past_due": 0,
         "amount": 950.00
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
         "external_id": "NOMINA-202406-38893",
         "origination_date": "2024-05-31",
         "cutoff_date": "2026-01-15",
         "status": "active",
         "is_eligible": true,
         "employer_name": "Merlin Properties SOCIMI",
         "employer_tax_id": "ESA86648867",
         "net_monthly_salary": 3200.00,
         "advance_amount": 1800.00,
         "outstanding_amount": 900.00,
         "repaid_amount": 900.00,
         "fee_percentage": 2.5,
         "fee_amount": 45.00,
         "days_past_due": 0,
         "maturity_date": "31/01/2025",
         "amount": 1800.00
         },
         {
         "external_id": "NOMINA-202406-30379",
         "origination_date": "2024-06-27",
         "cutoff_date": "2026-01-15",
         "status": "active",
         "is_eligible": true,
         "employer_name": "BBVA S.A.",
         "employer_tax_id": "ESA48265169",
         "net_monthly_salary": 4500.00,
         "advance_amount": 2500.00,
         "outstanding_amount": 0.00,
         "repaid_amount": 2500.00,
         "fee_percentage": 2.0,
         "fee_amount": 50.00,
         "days_past_due": 0,
         "maturity_date": "31/01/2025",
         "amount": 2500.00
         },
         {
         "external_id": "NOMINA-202406-70217",
         "origination_date": "2024-06-12",
         "cutoff_date": "2026-01-15",
         "status": "past_due",
         "is_eligible": true,
         "employer_name": "Naturgy Energy S.A.",
         "employer_tax_id": "ESA08015497",
         "net_monthly_salary": 2800.00,
         "advance_amount": 1200.00,
         "outstanding_amount": 1200.00,
         "repaid_amount": 0.00,
         "fee_percentage": 3.0,
         "fee_amount": 36.00,
         "days_past_due": 35,
         "maturity_date": "31/12/2024",
         "amount": 1200.00
         },
         {
         "external_id": "NOMINA-202406-16006",
         "origination_date": "2024-06-09",
         "cutoff_date": "2026-01-15",
         "status": "ACTIVE",
         "is_eligible": true,
         "employer_name": "Naturgy Energy S.A.",
         "employer_tax_id": "ESA08015497",
         "net_monthly_salary": 3500.00,
         "advance_amount": 3000.00,
         "outstanding_amount": 1500.00,
         "repaid_amount": 1500.00,
         "fee_percentage": 2.5,
         "fee_amount": 75.00,
         "days_past_due": 0,
         "maturity_date": "28/02/2025",
         "amount": 3000.00
         },
         {
         "external_id": "NOMINA-202406-57819",
         "origination_date": "2024-06-27",
         "cutoff_date": "2026-01-15",
         "status": "active",
         "is_eligible": true,
         "employer_name": "Acciona S.A.",
         "employer_tax_id": "ESA08001851",
         "net_monthly_salary": 3800.00,
         "advance_amount": 2200.00,
         "outstanding_amount": 733.33,
         "repaid_amount": 1466.67,
         "fee_percentage": 2.0,
         "fee_amount": 44.00,
         "days_past_due": 0,
         "maturity_date": "31/03/2025",
         "amount": 2200.00
         },
         {
         "external_id": "NOMINA-202406-42087",
         "origination_date": "2024-06-21",
         "cutoff_date": "2026-01-15",
         "status": "written_off",
         "is_eligible": false,
         "employer_name": "Iberdrola S.A.",
         "employer_tax_id": "ESA48010615",
         "net_monthly_salary": 5200.00,
         "advance_amount": 4100.00,
         "outstanding_amount": 4100.00,
         "repaid_amount": 0.00,
         "fee_percentage": 2.5,
         "fee_amount": 102.50,
         "days_past_due": 150,
         "maturity_date": "31/08/2024",
         "amount": 4100.00
         },
         {
         "external_id": "NOMINA-202406-17331",
         "origination_date": "2024-06-29",
         "cutoff_date": "2026-01-15",
         "status": "active",
         "is_eligible": true,
         "employer_name": "CaixaBank S.A.",
         "employer_tax_id": "ESA08663619",
         "net_monthly_salary": 4800.00,
         "advance_amount": 1500.00,
         "outstanding_amount": 500.00,
         "repaid_amount": 1000.00,
         "fee_percentage": 1.8,
         "fee_amount": 27.00,
         "days_past_due": 0,
         "maturity_date": "28/02/2025",
         "amount": 1500.00
         },
         {
         "external_id": "NOMINA-202407-88421",
         "origination_date": "2024-07-14",
         "cutoff_date": "2026-01-15",
         "status": "settled",
         "is_eligible": false,
         "employer_name": "Telefonica S.A.",
         "employer_tax_id": "ESA28015865",
         "net_monthly_salary": 3600.00,
         "advance_amount": 2000.00,
         "outstanding_amount": 0.00,
         "repaid_amount": 2000.00,
         "fee_percentage": 2.0,
         "fee_amount": 40.00,
         "days_past_due": 0,
         "maturity_date": "31/08/2024",
         "amount": 2000.00
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