from __future__ import annotations

from pathlib import Path
import sqlite3

from .claims import load_claim_records, replace_claims_table


def run_pipeline(*, variant: str, input_root: Path, output_db: Path) -> None:
    claims = load_claim_records(input_root, variant=variant)
    output_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(output_db) as connection:
        replace_claims_table(connection, claims)
        connection.commit()
