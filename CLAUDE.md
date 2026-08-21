# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project

pyisomme is a Python library and CLI for the **ISO-MME** crash-test data format. It reads and writes
ISO-MME containers, processes signal channels, calculates injury criteria, plots results, and creates
PowerPoint assessment reports.

## Current work

Read project documents only when the user's active task concerns that project. Do not preload them for
unrelated work. When a listed project is completed, remove or update its entry in both `AGENTS.md` and
`CLAUDE.md` in the same change.

- [Report Architecture Review](docs/log/20260726_Report-Architecture-Review.md)

## Workflow

- Use `uv` for dependency management and `nox` for CI-equivalent checks. `uv run` uses the repository's `.venv`.
- Inspect nearby code and tests before editing. Keep changes within the user's requested scope and
  preserve unrelated working-tree changes.
- Do not commit unless the user explicitly asks. Leave changes for manual review and summarize changed
  files, verification performed, deviations, and open work.
- Writing methods overwrite without warning; verify output paths before using them.

## Commands

```powershell
uv sync --group dev
uv run python -m pytest tests
uv run python -m pytest tests/test_module.py
uv run python -m pytest tests/test_module.py::TestClass::test_method

uv run nox -s lint type_check
uv run nox -s tests-3.9
uv run nox -s tests-3.9 -- tests.test_module

uv run pyisomme --help
uv run pyisomme <command> --help
```

Some tests require untracked fixtures under `data/`; report exports write to `out/`. PowerPoint report
tests are opt-in:

```powershell
$env:PYISOMME_PPTX='1'; uv run pytest tests/test_report.py
$env:PYISOMME_PPTX='euro_ncap_side_pole'; uv run pytest tests/test_report.py
```

## Continuous integration

- [.github/workflows/ci.yml](.github/workflows/ci.yml) runs Nox linting, type checking, fixture-free
  report checks, and tests on Python 3.9–3.12.
- [.github/workflows/python-publish.yml](.github/workflows/python-publish.yml) reuses CI, builds and
  verifies distributions, and publishes tagged GitHub releases to PyPI. Manual dispatch is a build-only
  dry run.

Keep local verification aligned with these workflows. Do not alter publishing, secrets, or release
triggers unless the user explicitly requests it.

## Architecture

The public domain model is re-exported from [pyisomme/__init__.py](pyisomme/__init__.py):

- `Isomme` ([pyisomme/isomme.py](pyisomme/isomme.py)) represents one test container and dispatches
  reading and writing by source type.
- `Channel` ([pyisomme/channel.py](pyisomme/channel.py)) stores one signal and supports filtering,
  integration, differentiation, arithmetic, scaling, and unit conversion.
- `Code` ([pyisomme/code.py](pyisomme/code.py)) is a 16-character ISO-MME channel code. Definitions and
  default units are in [pyisomme/channel_codes.xml](pyisomme/channel_codes.xml).

`Isomme.get_channel()` and `get_channels()` are the primary lookup APIs. They match wildcard code
patterns and can lazily filter, calculate, differentiate, or integrate missing derived channels. Add new
derived calculations to the dispatch in `Isomme.get_channel()` and implement their math under
[pyisomme/calculate/](pyisomme/calculate/).

Other main areas:

- [pyisomme/report/](pyisomme/report/) — assessment criteria and PowerPoint reports
- [pyisomme/plotting/](pyisomme/plotting/) — matplotlib plots and tables
- [head-trajectory-calculation/](head-trajectory-calculation/) — standalone bundled subproject

## Conventions

- Use `logging.getLogger(__name__)`; prefer logging over `print` in library code.
- Use `from __future__ import annotations` and preserve the repository's typing style.
- Import public report-page and plotting classes from their package re-exports, not implementation
  modules.
- Handle units through [pyisomme/unit.py](pyisomme/unit.py). Convert with `Channel.convert_unit()`;
  never assign raw Astropy units to `Channel.unit` or mutate channel data to convert units. In
  report criteria, convert `self.channel` to the desired unit before reading its data, then use
  `self.channel.get_data()` without a `unit=` override. Otherwise `criterion.value` is in a
  different unit from the `criterion.channel.unit` shown by `Report.print_results()`.
- Keep `ruff` and `mypy` clean. `mypy` is intentionally scoped in [pyproject.toml](pyproject.toml).
- Supported measurement inputs are `.mme`, `.chn`, channel-data files such as `.001`, directories, and
  supported archives; unrelated media files are ignored.
- `objective_rating_metrics` is a PyPI dependency declared in [pyproject.toml](pyproject.toml), not
  vendored code.
