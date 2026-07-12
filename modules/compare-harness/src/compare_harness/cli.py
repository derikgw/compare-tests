from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from compare_harness.application.configuration import load_harness_config
from compare_harness.application.service import CompareHarnessService


def main() -> None:
    parser = argparse.ArgumentParser(prog="compare-harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run baseline/candidate ETL compare.")
    run_parser.add_argument("--config-dir", default=None, help="Configuration directory. Overrides APP_CONFIG_DIR.")
    run_parser.add_argument("--profile", default=None, help="sprig-config profile.")

    args = parser.parse_args()
    if args.command == "run":
        config = load_harness_config(config_dir=args.config_dir, profile=args.profile)
        service = CompareHarnessService(config)
        result = service.run()
        print(json.dumps(asdict(result), indent=2, default=str))


if __name__ == "__main__":
    main()
