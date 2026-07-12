# Compare Harness Architecture

## Goals

- keep compare harness dependencies isolated from ETL dependencies
- run baseline and candidate ETL versions as subprocesses
- apply configurable, pluggable compare phases
- preserve clean boundaries (domain/application/adapters)

## Module Boundaries

- `domain`
  - compare models (`Finding`, `PhaseResult`, context)
  - phase protocol contract
- `application`
  - configuration parsing (`sprig-config`, `APP_CONFIG_DIR`)
  - pipeline orchestration and run service
- `adapters`
  - subprocess command execution
  - SQLite data loading
  - built-in phase implementations

## Execution Flow

1. Load merged config from `application.yml` + profile.
2. Resolve phase pack imports from `compare.phase_imports`.
3. Run ETL baseline command (isolated env).
4. Run ETL candidate command (isolated env).
5. Load baseline/candidate tables from SQLite outputs.
6. Execute configured phase pipeline in order.
7. Emit structured results.
