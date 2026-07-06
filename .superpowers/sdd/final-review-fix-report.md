# Final Review Fix Report

## Summary

- Fixed `ixfdoc setup skills` for installed wheel/package usage by resolving wrapper sources from package resources with `importlib.resources` instead of deriving the repository root from `__file__`.
- Added package resource wrapper copies under `src/ixunfei_docx_reader/_resources/skills/...` and configured the wheel package target so the resources ship with the package.
- Added a release-path smoke test that builds a wheel, installs it into a fresh virtual environment, and verifies `ixfdoc setup skills --runtimes codex --json` installs the packaged Codex wrapper.
- Normalized Windows cookie export failures to sanitized `RuntimeError`s for missing/empty `_csrf_token`, malformed Local State JSON/base64, AES-GCM decrypt failures, Unicode decode failures, and DPAPI failures.
- Marked Windows as CI-tested / experimental in documentation until live Windows LarkShell validation exists.
- Updated CI so Windows installs `.[dev,windows]` and imports `win32crypt`.
- Added CLI contract coverage so unsupported `ixfdoc setup skills --runtimes` values emit structured JSON errors rather than tracebacks.

## Files Changed

- `.github/workflows/ci.yml`
- `README.md`
- `docs/supported-platforms.md`
- `pyproject.toml`
- `src/ixunfei_docx_reader/cli.py`
- `src/ixunfei_docx_reader/cookies/windows_larkshell.py`
- `src/ixunfei_docx_reader/setup.py`
- `src/ixunfei_docx_reader/_resources/skills/codex/ixunfei-docx-reader/SKILL.md`
- `src/ixunfei_docx_reader/_resources/skills/claude-code/ixunfei-docx-reader/SKILL.md`
- `tests/test_cli_contract.py`
- `tests/test_setup.py`
- `tests/test_windows_cookie_provider.py`

## Commands And Results

- `python -m pytest tests/test_setup.py::test_built_wheel_setup_skills_can_install_packaged_codex_wrapper tests/test_windows_cookie_provider.py::test_export_cookies_from_db_raises_when_csrf_cookie_is_missing tests/test_windows_cookie_provider.py::test_load_local_state_master_key_normalizes_empty_json tests/test_windows_cookie_provider.py::test_load_local_state_master_key_normalizes_malformed_base64 tests/test_windows_cookie_provider.py::test_unwrap_local_state_key_normalizes_dpapi_failures -q`
  - Result: `5 passed in 16.52s`
- `python -m pytest tests/test_setup.py tests/test_cli_contract.py tests/test_windows_cookie_provider.py -q`
  - Initial result after first package metadata edit: `1 failed, 48 passed in 4.64s`
  - Root cause: Hatch wheel build rejected duplicate `force-include` entries because `_resources` files were already inside the package.
- `python -m build --wheel --outdir /tmp/ixfdoc-build-debug`
  - Result: reproduced Hatch duplicate wheel path error and confirmed the packaging root cause.
- `python -m pytest tests/test_setup.py tests/test_cli_contract.py tests/test_windows_cookie_provider.py -q`
  - Result after removing duplicate `force-include`: `49 passed in 13.99s`
- `python -m pip install -e ".[dev]"`
  - Result: editable install succeeded.
- `python -m compileall -q src`
  - Result: passed with no output.
- `python -m pytest -q`
  - Result: `61 passed in 14.71s`
- `python -m ruff check .`
  - Result: `All checks passed!`
- `python -m build`
  - Result: `Successfully built ixunfei_docx_reader-0.1.0.tar.gz and ixunfei_docx_reader-0.1.0-py3-none-any.whl`
- `scripts/smoke.sh`
  - Result: `61 passed in 14.23s` and `ixfdoc 0.1.0`
- `python -m compileall -q src && python -m pytest tests/test_cli_contract.py::test_setup_skills_invalid_runtime_without_json_returns_json_error -q`
  - Result: compile passed; focused CLI contract test `1 passed in 0.10s`

## Remaining Risks

- Live Windows LarkShell cookie export is still not validated on an actual Windows desktop session; documentation now marks Windows as CI-tested / experimental.
- Local verification ran on macOS, so the Windows `pywin32` import step is covered by CI configuration but was not executed locally.
