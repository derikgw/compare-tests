from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    member_id: str
    claim_type: str
    total_charge: float
    line_count: int
    updated_at: str


def run_pipeline(*, variant: str, input_root: Path, output_db: Path) -> None:
    claims = _load_claim_records(input_root, variant=variant)
    output_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(output_db) as connection:
        _create_schema(connection)
        connection.execute("DELETE FROM claims")
        connection.executemany(
            "INSERT INTO claims (claim_id, member_id, claim_type, total_charge, line_count, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    claim.claim_id,
                    claim.member_id,
                    claim.claim_type,
                    claim.total_charge,
                    claim.line_count,
                    claim.updated_at,
                )
                for claim in claims
            ],
        )
        connection.commit()


def _load_claim_records(input_root: Path, *, variant: str) -> list[ClaimRecord]:
    records: list[ClaimRecord] = []
    for json_file in sorted(input_root.rglob("*.json")):
        payload = json.loads(json_file.read_text(encoding="utf-8"))
        claims = payload.get("claims", [])
        if not isinstance(claims, list):
            raise ValueError(f"Expected list at claims[] in {json_file}")
        for claim in claims:
            records.append(_transform_claim(claim, variant=variant))
    return records


def _transform_claim(claim: dict[str, object], *, variant: str) -> ClaimRecord:
    lines = claim.get("lines", [])
    if not isinstance(lines, list):
        raise ValueError("Claim lines must be a list.")
    line_charge_total = 0.0
    for line in lines:
        if not isinstance(line, dict):
            continue
        line_charge_total += float(line.get("line_charge", 0))

    total_charge = line_charge_total
    if variant == "candidate":
        # Intentional behavior difference for compare testing.
        total_charge = round(total_charge * 1.01, 2)

    return ClaimRecord(
        claim_id=str(claim["claim_id"]),
        member_id=str(claim.get("member_id", "")),
        claim_type=str(claim.get("claim_type", "")),
        total_charge=total_charge,
        line_count=len(lines),
        updated_at=str(claim.get("updated_at", "")),
    )


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            total_charge REAL NOT NULL,
            line_count INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
