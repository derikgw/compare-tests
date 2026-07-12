from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    member_id: str
    claim_type: str
    line_count: int
    lines: str
    diagnosis_codes: str
    updated_at: str


def load_claim_records(input_root: Path, *, variant: str) -> list[ClaimRecord]:
    _ = variant
    records: list[ClaimRecord] = []
    for json_file in sorted(input_root.rglob("*.json")):
        payload = json.loads(json_file.read_text(encoding="utf-8"))
        claims = payload.get("claims", [])
        if not isinstance(claims, list):
            raise ValueError(f"Expected list at claims[] in {json_file}")
        for claim in claims:
            records.append(_transform_claim(claim))
    return records


def _transform_claim(claim: dict[str, object]) -> ClaimRecord:
    lines = claim.get("lines", [])
    if not isinstance(lines, list):
        raise ValueError("Claim lines must be a list.")
    diagnosis_codes = claim.get("diagnosis_codes", [])
    if not isinstance(diagnosis_codes, list):
        raise ValueError("Claim diagnosis_codes must be a list.")

    return ClaimRecord(
        claim_id=str(claim["claim_id"]),
        member_id=str(claim.get("member_id", "")),
        claim_type=str(claim.get("claim_type", "")),
        line_count=len(lines),
        lines=json.dumps(lines, ensure_ascii=False, separators=(",", ":")),
        diagnosis_codes=json.dumps(diagnosis_codes, ensure_ascii=False, separators=(",", ":")),
        updated_at=str(claim.get("updated_at", "")),
    )
