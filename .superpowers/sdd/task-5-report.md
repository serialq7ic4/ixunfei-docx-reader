# Task 5 Report: Windows DPAPI Cookie Export

## Implementation Summary

- Added the `windows` optional dependency group with `pywin32>=306` guarded to Windows platforms.
- Implemented Windows cookie row conversion with an injectable byte decryptor.
- Implemented read-only SQLite cookie export using `mode=ro`, host filtering, deterministic ordering, browser-cookie JSON output, and best-effort `0600` output permissions.
- Implemented DPAPI decryption through `win32crypt.CryptUnprotectData` with an actionable missing-`pywin32` error.
- Updated `export_cookies()` to resolve the LarkShell cookie DB from an explicit path, injected `app_data`, or `%APPDATA%`.
- Wired `--host-like` through the Windows CLI provider path.
- Narrowed the Windows CLI provider exception handling to expected file, runtime, SQLite, and OS errors.
- Updated supported-platform docs with Windows install and export guidance and retained the explicit no-Linux-support stance.

## Test Results

- `python -m pytest tests/test_windows_cookie_provider.py -q`
  - Result: PASS, 8 passed.
- `python -m pytest tests/test_cli_contract.py -q`
  - Result: PASS, 14 passed.
- `python -m compileall -q src && python -m pytest -q`
  - Result: PASS, 38 passed.
- `git diff --check`
  - Result: PASS.

## TDD Evidence

- Added `row_to_cookie` tests first.
  - Initial focused run failed during collection because `row_to_cookie` did not exist.
  - Implemented the minimal conversion function and reran provider tests successfully.
- Added `export_cookies_from_db` SQLite export test first.
  - Initial focused run failed during collection because `export_cookies_from_db` did not exist.
  - Implemented the read-only SQLite exporter and reran focused tests.
- Added an APPDATA fallback regression test after self-review found the CLI/provider default path gap.
  - Implemented the `%APPDATA%` lookup and reran focused plus full verification.

## Files Changed

- `pyproject.toml`
- `src/ixunfei_docx_reader/cookies/windows_larkshell.py`
- `src/ixunfei_docx_reader/cli.py`
- `tests/test_windows_cookie_provider.py`
- `tests/test_cli_contract.py`
- `docs/supported-platforms.md`
- `.superpowers/sdd/task-5-report.md`

## Self-Review

- Completeness: Matches Task 5 scope: dependency, row conversion, SQLite export, injectable decryptor tests, DPAPI decryptor, CLI pass-through, docs, verification, and report.
- Overbuilding: No daemon, GUI, browser extension, telemetry, Linux support, hidden state, or extra cookie formats were added.
- Read-only/local behavior: SQLite uses `file:<path>?mode=ro`; provider reads local files and writes only the requested output JSON.
- Cookie secrecy: Tests, docs, stdout/stderr assertions, and report avoid exposing real cookie values. Tests use synthetic placeholders only.
- Existing patterns: Provider output matches the project’s existing browser-cookie JSON list shape and metadata return pattern.
- Error handling: Windows CLI branch now catches expected failures instead of broad `Exception`.

## Concerns

- Real Windows DPAPI cannot be live-tested on this macOS environment. Coverage uses injectable decryptor and mocked DPAPI entrypoint behavior for deterministic validation.
- The DPAPI implementation follows the Task 5 requirement for DPAPI-protected cookie values directly; if future Chromium/LarkShell versions use an additional Local State AES key flow, that should be implemented as a separate task with Windows fixtures.
