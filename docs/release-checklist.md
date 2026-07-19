# Release Checklist

This checklist is intentionally lightweight for an early-stage project and can be
expanded over time.

## 1) Prepare

- Confirm target scope and module(s) for the release.
- Review open bugs/regressions that should block release.
- Ensure version bump plan is clear for affected module `pyproject.toml` files.

## 2) Validate locally

```bash
pytest modules/compare-core/tests
pytest modules/compare-harness/tests
pytest modules/etl-app/tests
```

- Run a representative harness execution if behavior changed:

```bash
cd modules/compare-harness
compare-harness run --profile local
```

## 3) Update docs

- Update module README files if usage changed.
- Add notable behavior/config changes to docs under `docs/harness/` as needed.

## 4) Version and tag

- Update version(s) in relevant `pyproject.toml` file(s).
- Merge approved PR(s) to `main`.
- Create an annotated tag from `main`.

Example:

```bash
git checkout main
git pull
git tag -a v0.x.y -m "Release v0.x.y"
git push origin v0.x.y
```

## 5) Publish release notes

- Summarize fixes/features/breaking changes.
- Include migration notes and config changes.
- Link key issues/PRs.

## 6) Post-release checks

- Verify CI on tag/release branch.
- Smoke test a fresh clone setup path.
- Capture follow-up items for the next milestone.