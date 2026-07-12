# Compare Harness Change Log

## 0.1.0

- Added monorepo module split:
  - `modules/compare-harness`
  - `modules/etl-app`
- Added `sprig-config` based harness configuration with `APP_CONFIG_DIR` support
- Added pluggable phase pipeline with built-in phases:
  - schema
  - datatype
  - hash
  - rowdiff
- Added x12-json style ETL guinea pig that writes SQLite output
