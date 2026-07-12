# etl-app

Guinea pig ETL module that reads local x12-json files and materializes SQLite output.

## Run

```bash
etl-app run --input-root ./data/raw --output-db ./runs/output.db
```

Optional: `--variant candidate` enables the compare-demo behavior.

## Scripts

The `scripts/` folder provides ETL-only CLI helpers:

```bash
./scripts/run.sh
./scripts/clean.sh
./scripts/inspect-db.sh
```

Optional args:

- `run.sh [input_root] [output_db]`
- `clean.sh [runs_dir]`
- `inspect-db.sh [db_path] [table_name] [limit_rows]`
