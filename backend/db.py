import os
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/organ_allocation")


@contextmanager
def connection():
    """Yield a transaction-scoped connection; psycopg commits or rolls back on exit."""
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


def initialize_schema():
    schema = Path(__file__).resolve().parents[1] / "schema.sql"
    with connection() as conn:
        conn.execute(schema.read_text(encoding="utf-8"), prepare=False)
