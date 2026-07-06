# Task 1 Report: Add Lightweight Skill Setup Command

## Implementation Summary

- Added `src/ixunfei_docx_reader/setup.py` as the source of truth for lightweight skill wrapper setup.
- Implemented `RuntimeTarget`, `detect_runtime_targets`, `normalize_runtimes`, and `install_skill_wrappers`.
- Added `ixfdoc setup skills` CLI support with `--runtimes`, `--force`, and `--json`.
- Kept Codex and Claude Code skill wrappers as copied source assets; no wrapper logic was expanded.

## TDD Evidence

- RED: `python -m pytest tests/test_setup.py -q`
  - Failed with `ModuleNotFoundError: No module named 'ixunfei_docx_reader.setup'`.
- GREEN: `python -m pytest tests/test_setup.py -q`
  - Passed after adding runtime target detection.
- RED: `python -m pytest tests/test_setup.py -q`
  - Failed with `ImportError: cannot import name 'install_skill_wrappers'`.
- GREEN: `python -m pytest tests/test_setup.py -q`
  - Passed after adding minimal wrapper installer behavior.
- RED: `python -m pytest tests/test_cli_contract.py::test_setup_skills_json_outputs_machine_readable_status -q`
  - Failed with invalid command choice for `setup`.
- GREEN: `python -m pytest tests/test_cli_contract.py::test_setup_skills_json_outputs_machine_readable_status tests/test_setup.py -q`
  - Passed after wiring `ixfdoc setup skills`.

## Test Results

- `python -m pytest tests/test_setup.py tests/test_cli_contract.py -q`
  - `16 passed in 31.81s`
- `git diff --check`
  - Passed with no output.
- `python -m pytest -q`
  - `28 passed in 2.90s`

## Files Changed

- Created `src/ixunfei_docx_reader/setup.py`
- Created `tests/test_setup.py`
- Modified `src/ixunfei_docx_reader/cli.py`
- Modified `tests/test_cli_contract.py`

## Self-Review

- Completeness: Meets the Task 1 interfaces and CLI command requirements from the brief.
- Overbuilding: Implementation is intentionally small and task-scoped; no extra runtime discovery, validation layers, or wrapper behavior were added.
- Test quality: Tests cover environment override detection, default target detection, selected-runtime install, overwrite refusal, and JSON CLI contract.
- Existing patterns: CLI parsing and subprocess contract tests follow the existing project style.

## Concerns

- `auto` and `all` currently normalize to both supported runtimes whether or not local runtime directories already exist, matching the brief's provided implementation.
