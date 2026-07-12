# compare-harness

Comparison harness for running baseline/candidate ETL executions and applying pluggable compare phases.

## Configuration

The harness uses `sprig-config` and resolves configuration directories in this order:

1. explicit `--config-dir`
2. `APP_CONFIG_DIR`
3. default `./config`

Profiles are loaded with `--profile` and phase packs are configured with `compare.phase_imports`.

## Run

```bash
python -m pip install -e ../compare-core
compare-harness run --profile local
```

By default, baseline ETL code is checked out into `config/runs/worktrees/baseline-repo` inside this module, while candidate ETL runs from `modules/etl-app`.

## Scripts

```bash
./scripts/run-baseline-etl.sh
./scripts/run-candidate-etl.sh
./scripts/run-compare.sh
./scripts/clean-runs.sh
```
