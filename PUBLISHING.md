# Publishing `sledge` to PyPI

Short release runbook. Publishing stays a human step — a PyPI version is
immutable and can never be reused, so the final `twine upload` is never automated.

- **Distribution name:** `sledge-prover` (the bare `sledge` name may be taken).
- **Import name / commands:** `sledge`, `sledge-mcp`.

> 中文速记：改版本号（两处一致）→ 测试 → 构建 → `twine check` → 先发 TestPyPI 验证 → 再发正式 PyPI → 打 git tag。版本一旦上线不可覆盖。

## One-time setup

Create accounts + API tokens on [PyPI](https://pypi.org/) and
[TestPyPI](https://test.pypi.org/); store them in `~/.pypirc` (chmod 600):

```ini
[pypi]
  username = __token__
  password = pypi-...          # PyPI token
[testpypi]
  username = __token__
  password = pypi-...          # TestPyPI token
```

Install tooling: `pip install -e ".[dev]"` (brings build + twine).

## Release steps

1. **Bump the version in two places (must match):**
   - `pyproject.toml` → `version = "X.Y.Z"`
   - `src/sledge/__init__.py` → `__version__ = "X.Y.Z"`

   Verify: `python -c "import sledge; print(sledge.__version__)"`

2. **Test:** `pytest -q`  (all green)
3. **Build:** `rm -rf dist build src/*.egg-info && python -m build`
4. **Validate:** `python -m twine check dist/*`  (both PASSED)
5. **TestPyPI dry run:**
   ```bash
   python -m twine upload --repository testpypi dist/*
   python -m venv /tmp/s && /tmp/s/bin/pip install \
     -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ \
     "sledge-prover[mcp]"
   /tmp/s/bin/sledge --version && rm -rf /tmp/s
   ```
6. **Publish:** `python -m twine upload dist/*`
7. **Tag:** `git tag -a vX.Y.Z -m "sledge vX.Y.Z" && git push origin vX.Y.Z`

## Notes

- **Immutable:** you can't overwrite a version. Broken release → yank it and ship
  a new patch. Use `X.Y.ZrcN` for pre-releases.
- **Do you even need PyPI?** People can already
  `pip install "git+https://github.com/MeghanBao/sledge.git#egg=sledge-prover[mcp]"`.
  Publish when you want a frictionless `pip install sledge-prover` and to reserve
  the name — not before the API settles.
