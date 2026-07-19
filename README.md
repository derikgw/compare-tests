# compare-tests
Compare test facility for comparing an old (baseline) version of etl software output vs. newer (candidate) version of output.

This project is intentionally early-stage. Interfaces, conventions, and contribution
processes are expected to evolve as real ETL use cases and community feedback arrive.

The project includes a small hexagonal compare core that:

- checks out `main` as the default baseline, with support for tag or commit-hash overrides
- runs the baseline before the current workspace candidate
- reports schema additions and removals
- reports side-by-side baseline and candidate values for every column in each compared row
- supports excluded columns while still showing the full record and marking excluded fields in the report

## Monorepo modules

- `modules/compare-core`: shared compare core (`compare_tests`) for schema and row-level report generation
- `modules/compare-harness`: isolated compare harness runtime (sprig-config based, pluggable compare phases)
- `modules/etl-app`: isolated guinea-pig ETL app (x12-json input with nested arrays -> SQLite outputs)

Each module has its own `pyproject.toml` and dependency graph to avoid cross-contamination.

## Harness documentation

- `docs/harness/architecture.md`
- `docs/harness/configuration.md`
- `docs/harness/usage.md`
- `docs/harness/troubleshooting.md`
- `docs/harness/change-log.md`

## Project operations

- `docs/release-checklist.md`

## Quickstart

### Prerequisites

- Python 3.10+
- Git

### Install (editable monorepo setup)

```bash
python -m pip install -U pip
python -m pip install -e modules/compare-core
python -m pip install -e "modules/compare-harness[dev]"
python -m pip install -e "modules/etl-app[dev]"
```

### Run compare harness

```bash
cd modules/compare-harness
compare-harness run --profile local
```

Output and worktree defaults:

- baseline checkout: `modules/compare-harness/output/worktrees/baseline-repo`
- candidate ETL source: `modules/etl-app`
- run artifacts: `modules/compare-harness/output`

### Run tests

```bash
pytest modules/compare-core/tests
pytest modules/compare-harness/tests
pytest modules/etl-app/tests
```

## Open source notes

- Contributions are welcome, including bug reports, tests, and docs improvements.
- The project currently optimizes for practical ETL iteration speed over rigid process.
- As usage grows, release/versioning and compatibility policies will be tightened.

See:

- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
