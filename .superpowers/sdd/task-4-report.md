# Task 4 Report: Add Windows Cookie Provider Skeleton

## Implementation Summary

- Added `src/ixunfei_docx_reader/cookies/windows_larkshell.py` with:
  - `DEFAULT_HOST_LIKE = "%xfchat.iflytek.com%"`
  - `find_cookie_db(cookies_db, app_data)` discovery for explicit paths and default Windows LarkShell APPDATA locations.
  - Temporary `export_cookies(...)` skeleton that confirms the DB exists, then intentionally raises `RuntimeError("Windows cookie decryption is not implemented yet.")`.
- Updated `src/ixunfei_docx_reader/cli.py` to:
  - Accept `--provider windows-larkshell`.
  - Route `--provider auto` to `windows-larkshell` when `platform.system().lower()` resolves to Windows.
  - Route explicit Windows exports to the Windows provider skeleton.
  - Preserve existing macOS behavior and failure handling.
- Added provider and CLI tests covering discovery, missing DB failures, explicit Windows provider CLI acceptance, auto-routing on Windows, and the intentional not-yet-implemented export behavior.
- Did not implement DPAPI decryption or SQLite cookie export for Windows; that remains intentionally deferred to Task 5.

## Test Results

- `python -m pytest tests/test_windows_cookie_provider.py -q`
  - Initial RED: failed with `ModuleNotFoundError: No module named 'ixunfei_docx_reader.cookies.windows_larkshell'`.
  - GREEN after skeleton: `2 passed in 0.01s`.
- `python -m pytest tests/test_cli_contract.py::test_cookies_export_accepts_windows_larkshell_provider -q`
  - Initial RED: failed because argparse rejected `windows-larkshell` with return code `2`.
  - GREEN after CLI routing: covered in focused suite.
- `python -m pytest tests/test_cli_contract.py::test_cookies_export_auto_routes_to_windows_provider -q`
  - Initial collection issue after adding coverage: missing `pytest` import.
  - GREEN after import fix: `1 passed in 0.04s`.
- `python -m pytest tests/test_windows_cookie_provider.py tests/test_cli_contract.py -q`
  - Final focused result: `17 passed in 1.22s`.
- `python -m pytest -q`
  - Final full-suite result: `33 passed in 1.12s`.
- `git diff --check`
  - Passed.
- `python -m ruff check src tests`
  - Passed: `All checks passed!`.

## TDD Evidence

- Provider discovery tests were written before creating `windows_larkshell.py`; the focused provider test failed with the expected missing-module error.
- The minimal provider discovery implementation was added only after the RED check, then the focused provider test passed.
- The explicit CLI provider test was written before CLI provider choices were updated; it failed because argparse rejected `windows-larkshell`.
- CLI provider routing was then wired minimally to pass the test without implementing Windows DPAPI.
- Additional scoped tests were added for Windows auto-routing and the intentional placeholder export failure to cover the full Task 4 contract.

## Files Changed

- Created: `src/ixunfei_docx_reader/cookies/windows_larkshell.py`
- Created: `tests/test_windows_cookie_provider.py`
- Modified: `src/ixunfei_docx_reader/cli.py`
- Modified: `tests/test_cli_contract.py`
- Created: `.superpowers/sdd/task-4-report.md`

## Self-Review

- Completeness: Task 4 requirements are covered: provider discovery, CLI provider routing, explicit provider support, Windows auto-routing, tests, and placeholder non-DPAPI export behavior.
- Scope control: No DPAPI implementation, Chromium row reading, Windows decryption, or cookie JSON export behavior was added.
- Test quality: Tests cover both direct provider functions and observable CLI behavior. Auto-routing is tested through `cli.main` with monkeypatched platform detection and provider function.
- Existing patterns: CLI error handling uses existing `fail(...)` JSON stderr contract and exit code `6`; macOS route remains unchanged.
- Overbuilding check: Added only the skeleton and small contract tests needed for Task 4.

## Concerns

- None.

## Review Fix: export_cookies Positional Output

### Fix Summary

- Updated `src/ixunfei_docx_reader/cookies/windows_larkshell.py` so `export_cookies` accepts `output` as the first positional parameter, matching the Task 4 brief contract.
- Added focused regression coverage in `tests/test_windows_cookie_provider.py` for calling `export_cookies(tmp_path / "cookies.json", cookies_db=db)`.
- Kept behavior task-scoped: the provider still verifies the cookie DB path and intentionally raises `RuntimeError("Windows cookie decryption is not implemented yet.")`; no DPAPI or SQLite export was implemented.

### Verification Results

- `python -m pytest tests/test_windows_cookie_provider.py::test_export_cookies_accepts_output_as_positional_argument -q`
  - RED before fix: failed with `TypeError: export_cookies() takes 0 positional arguments but 1 positional argument (and 1 keyword-only argument) were given`.
- `python -m pytest tests/test_windows_cookie_provider.py tests/test_cli_contract.py -q`
  - Final result: `18 passed in 1.27s`.
- `python -m ruff check .`
  - Final result: `All checks passed!`.
