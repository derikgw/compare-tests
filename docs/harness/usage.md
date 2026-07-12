# Compare Harness Usage

## Install module dependencies

```bash
cd modules/compare-core
python -m pip install -e .

cd modules/compare-harness
python -m pip install -e .
```

## Run with local profile

```bash
compare-harness run --profile local
```

Baseline ETL checkout defaults to:

- `modules/compare-harness/config/runs/worktrees/baseline-repo`

Candidate ETL source defaults to:

- `modules/etl-app`

## Override config directory

```bash
APP_CONFIG_DIR=/path/to/config compare-harness run --profile local
```

## Helper scripts

```bash
cd modules/compare-harness
./scripts/run-baseline-etl.sh
./scripts/run-candidate-etl.sh
./scripts/run-compare.sh
./scripts/clean-runs.sh
```

## Isolated ETL dependencies

Harness runs ETL as shell commands using module-local `PYTHONPATH` values:

- baseline from the checked-out baseline worktree
- candidate from `etl.working_dir` (default `modules/etl-app`)

This keeps compare-harness logic separate from ETL app concerns and avoids dependency contamination.
