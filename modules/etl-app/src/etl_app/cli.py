from __future__ import annotations

import argparse
import os
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(prog="etl-app")
    parser.add_argument("run", nargs="?", default="run")
    parser.add_argument(
        "--variant",
        choices=("default", "baseline", "candidate"),
        default=os.getenv("ETL_VARIANT", "default"),
    )
    parser.add_argument("--input-root", default=os.getenv("ETL_INPUT_ROOT", "./data/raw"))
    parser.add_argument("--output-db", default=os.getenv("ETL_OUTPUT_DB", "./runs/output.db"))
    args = parser.parse_args()
    run_pipeline(
        variant=args.variant,
        input_root=Path(args.input_root).resolve(),
        output_db=Path(args.output_db).resolve(),
    )


if __name__ == "__main__":
    main()
