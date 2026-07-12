# compare-tests
Compare test facility for comparing an old (baseline) version of etl software output vs. newer (candidate) version of output.

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
