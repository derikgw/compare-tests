# Compare Harness Troubleshooting

## `sprig-config` cannot find config

- verify `APP_CONFIG_DIR` points to `modules/compare-harness/config`
- or pass `--config-dir`

## Baseline/candidate ETL command fails

- run commands manually in `modules/etl-app`
- confirm output SQLite path is writable
- verify command uses its own environment/dependencies

## Baseline ETL directory not found in checked out ref

- verify `etl.baseline_ref` points to a ref that contains `etl.baseline_working_subpath`
- default expected path is `modules/etl-app` in the baseline checkout

## Missing phase id in pipeline

- every id listed in `compare.pipeline` must be declared in imported phase packs

## SQLite table load failure

- confirm ETL produced expected table name for dataset
- verify `compare.datasets[].table` matches generated table
