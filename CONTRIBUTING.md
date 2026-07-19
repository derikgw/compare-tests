# Contributing

Thanks for considering a contribution.

This is a new project and we expect tooling, conventions, and review standards to
change as usage increases. The goal right now is to keep contributions clear,
tested, and easy to review.

## Ground rules

- Keep changes scoped to one concern when possible.
- Add or update tests when behavior changes.
- Document user-facing behavior changes in README or docs.
- Prefer small pull requests over large batches.

## Local setup

From the repository root:

```bash
python -m pip install -U pip
python -m pip install -e modules/compare-core
python -m pip install -e "modules/compare-harness[dev]"
python -m pip install -e "modules/etl-app[dev]"
```

Optional (if you use Poetry):

```bash
poetry --version
```

Each module keeps its own `pyproject.toml` and dependency graph.

## Run tests

```bash
pytest modules/compare-core/tests
pytest modules/compare-harness/tests
pytest modules/etl-app/tests
```

## Pull requests

- Include a concise summary of the problem and change.
- Mention test coverage and commands executed.
- Link related issues, if any.
- Keep PR descriptions explicit about assumptions and tradeoffs.

## Reporting bugs

Please include:

- expected behavior
- actual behavior
- repro steps
- relevant config snippets
- stack traces or logs when available

## Code of conduct

By participating, you agree to follow `CODE_OF_CONDUCT.md`.