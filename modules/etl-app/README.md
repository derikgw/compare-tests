# etl-app

Guinea pig ETL module that reads local x12-json files and materializes SQLite output.

Current `claims` output stores nested arrays as serialized JSON text:

- `lines`
- `diagnosis_codes`

`claims` transform and table mapping live in `src/etl_app/claims/`.

## Run

```bash
etl-app run --input-root ./data/raw --output-db ./runs/output.db
```

`--variant` is accepted for runtime profile wiring, but current transform behavior is structure-preserving across variants.

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
