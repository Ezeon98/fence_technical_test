"""PostgreSQL connection and schema initialization."""

import json

import psycopg

from app.infrastructure.settings import get_settings


def get_connection() -> psycopg.Connection:
    """Open a PostgreSQL connection using configured URL."""
    settings = get_settings()
    return psycopg.connect(settings.database_url)


def initialize_database() -> None:
    """Create persistence schema when absent."""
    ddl = """
    CREATE TABLE IF NOT EXISTS covenant_reports (
        id SERIAL PRIMARY KEY,
        facility_id TEXT NOT NULL,
        as_of_date DATE NOT NULL,
        effective_rate TEXT NOT NULL,
        covenant_status TEXT NOT NULL,
        total_assets_evaluated INTEGER NOT NULL,
        included_asset_ids JSONB NOT NULL,
        excluded_assets_with_reasons JSONB NOT NULL,
        report_hash TEXT NOT NULL UNIQUE,
        blockchain_status TEXT NOT NULL DEFAULT 'PENDING',
        blockchain_tx_hash TEXT,
        blockchain_error TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(ddl)
        connection.commit()


def to_json(data: object) -> str:
    """Serialize Python object into JSON text for DB insertion."""
    return json.dumps(data, ensure_ascii=False)
