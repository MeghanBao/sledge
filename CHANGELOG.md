# Changelog

All notable changes to this project are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Statement validation (`validate_statement`): strips a stray outer pair of
  quotes and rejects a proposition containing a `"` that would break the
  generated `lemma "..."`. `prove`/`refute` now return a clear UNKNOWN
  ("invalid statement") instead of producing a broken theory.
- Integration test suite (`tests/test_integration.py`) that runs against a real
  Isabelle install and skips automatically when one isn't present.
- GitHub Actions CI: runs the test suite on Python 3.9/3.11/3.12 and validates
  the built distribution with `twine check`.
- `py.typed` marker so downstream users get the package's type hints.

## [0.1.0]

### Added
- `prove()` — cheap Isabelle tactics, then Sledgehammer (parse its suggested
  proof and re-check it, so VERIFIED always means a machine-checked proof).
- `refute()` — Nitpick/Quickcheck counterexample search → REFUTED.
- `check_theory()` — build a complete `.thy` verbatim.
- `IsabelleRunner` shelling out to `isabelle build`; honest UNKNOWN when Isabelle
  is absent (`ISABELLE_BINARY` to point at it).
- MCP server (`sledge-mcp`): tools `prove_statement` and `find_counterexample`.
- CLI `sledge prove | refute | check` with exit codes 0/1/2 and `--json`.
- Pure, tested theory generation and output parsing (FakeRunner, no Isabelle
  needed). READMEs in EN/ZH/DE; `PUBLISHING.md` runbook.
