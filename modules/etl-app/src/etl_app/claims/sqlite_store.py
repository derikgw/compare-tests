from __future__ import annotations

import sqlite3

from .transform import ClaimRecord


def replace_claims_table(connection: sqlite3.Connection, claims: list[ClaimRecord]) -> None:
    _create_claims_schema(connection)
    connection.execute("DELETE FROM claims")
    connection.executemany(
        "INSERT INTO claims (claim_id, member_id, claim_type, line_count, lines, diagnosis_codes, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                claim.claim_id,
                claim.member_id,
                claim.claim_type,
                claim.line_count,
                claim.lines,
                claim.diagnosis_codes,
                claim.updated_at,
            )
            for claim in claims
        ],
    )


def _create_claims_schema(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS claims")
    connection.execute(
        """
        CREATE TABLE claims (
            claim_id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            line_count INTEGER NOT NULL,
            lines TEXT NOT NULL,
            diagnosis_codes TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
