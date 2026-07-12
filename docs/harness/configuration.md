# Compare Harness Configuration

The harness uses `sprig-config`.

## Config directory resolution

1. `--config-dir`
2. `APP_CONFIG_DIR`
3. `./config`

## Base files

- `application.yml`
- `application-<profile>.yml`
- phase pack imports via `compare.phase_imports`

## Main keys

```yaml
etl:
  baseline_ref: main
  candidate_ref: workspace
  baseline_working_subpath: modules/etl-app
  baseline_checkout_dir: ./runs/worktrees/baseline-repo
  working_dir: ../etl-app
  baseline.command: ...
  candidate.command: ...
io.sqlite:
  baseline_db: ./runs/baseline/output.db
  candidate_db: ./runs/candidate/output.db
compare:
  phase_imports: [...]
  pipeline: [schema, datatype, hash, rowdiff]
  fail_fast: false
  datasets: [...]
```

## Phase pack format

```yaml
phase:
  id: schema
  enabled: true
  order: 100
  severity: high
  config: {}
```
