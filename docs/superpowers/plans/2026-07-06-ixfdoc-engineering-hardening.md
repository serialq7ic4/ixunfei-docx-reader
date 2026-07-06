# ixfdoc Engineering Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Turn `ixunfei-docx-reader` from a working local CLI into a small, installable, testable public project with thin Codex and Claude Code skill wrappers.

**Execution Status (2026-07-06):** Completed. The CLI-first package, Codex/Claude Code wrappers, CI, release workflow, macOS support, Windows experimental cookie provider, public docs, smoke scripts, and `v0.1.0` GitHub Release are implemented and verified. Follow-up outside this hardening plan: validate Windows cookie export on a real Windows LarkShell client before promoting Windows from experimental to Tier 1.

**Architecture:** Keep `ixfdoc` as the only source of truth for reading, cookie export, diagnostics, and conversion. Keep agent skills as thin wrapper instructions that call the CLI and follow its JSON error contract. Add only lightweight setup, CI, and platform-provider boundaries; do not add a daemon, browser extension, GUI, hidden state service, or multi-skill product framework.

**Tech Stack:** Python 3.11+, argparse, requests, pytest, GitHub Actions, macOS Keychain cookie export, planned Windows DPAPI cookie export.

## Global Constraints

- CLI command remains `ixfdoc`.
- Project name remains `ixunfei-docx-reader`.
- Supported desktop platforms are macOS now and Windows planned; do not add Linux support because i讯飞 has no Linux client.
- Codex and Claude Code support must be delivered as thin wrappers around `ixfdoc`, not separate parsers.
- Cookie values must never be printed in stdout, stderr, docs examples, tests, or logs.
- Generated Markdown/TSV and cookie files must be treated as sensitive local artifacts.
- Keep the design small: no daemon, GUI, telemetry, browser extension, SQLite state store, auto-update system, or marketplace-scale plugin framework.
- Prefer deterministic CLI behavior with tests over prompt-only skill behavior.
- Every task must keep `python -m pytest -q` passing.

---

## File Structure

- `src/ixunfei_docx_reader/cli.py` owns user-facing commands, JSON error output, `doctor`, `read`, `cookies export`, and new setup/status commands.
- `src/ixunfei_docx_reader/reader.py` owns private document fetching and source normalization.
- `src/ixunfei_docx_reader/converters/docx_markdown.py` owns Feishu/i讯飞 docx block-to-Markdown conversion.
- `src/ixunfei_docx_reader/cookies/macos_larkshell.py` owns macOS LarkShell cookie discovery and decryption.
- `src/ixunfei_docx_reader/cookies/windows_larkshell.py` will own Windows LarkShell cookie discovery and DPAPI decryption.
- `src/ixunfei_docx_reader/setup.py` will own runtime skill-directory detection and wrapper installation.
- `skills/codex/ixunfei-docx-reader/SKILL.md` remains the Codex wrapper source.
- `skills/claude-code/ixunfei-docx-reader/SKILL.md` remains the Claude Code wrapper source.
- `docs/supported-platforms.md` documents macOS/Windows support only.
- `docs/error-contract.md` documents stable machine-readable failure output.
- `.github/workflows/ci.yml` will run unit tests and compile checks on every push/PR.
- `.github/workflows/release.yml` will build release artifacts when tags are pushed.
- `tests/test_cli_contract.py` owns CLI behavior tests.
- `tests/test_setup.py` will own setup/runtime detection tests.
- `tests/test_windows_cookie_provider.py` will own Windows provider unit tests without needing a real Windows machine.

---

### Task 1: Add Lightweight Skill Setup Command

**Files:**
- Create: `src/ixunfei_docx_reader/setup.py`
- Modify: `src/ixunfei_docx_reader/cli.py`
- Test: `tests/test_setup.py`
- Test: `tests/test_cli_contract.py`

**Interfaces:**
- Consumes: wrapper sources at `skills/codex/ixunfei-docx-reader/SKILL.md` and `skills/claude-code/ixunfei-docx-reader/SKILL.md`
- Produces: `detect_runtime_targets(home: Path, env: Mapping[str, str]) -> list[RuntimeTarget]`
- Produces: `install_skill_wrappers(project_root: Path, home: Path, runtimes: list[str], force: bool, env: Mapping[str, str]) -> dict[str, object]`
- Produces CLI command: `ixfdoc setup skills --runtimes auto|codex|claude-code|all|none --force --json`

- [x] **Step 1: Write failing runtime detection tests**

```python
from pathlib import Path

from ixunfei_docx_reader.setup import detect_runtime_targets


def test_detect_runtime_targets_uses_env_over_defaults(tmp_path: Path) -> None:
    env = {
        "IXFDOC_CODEX_SKILLS_DIR": str(tmp_path / "codex-skills"),
        "IXFDOC_CLAUDE_CODE_SKILLS_DIR": str(tmp_path / "claude-skills"),
    }

    targets = detect_runtime_targets(tmp_path, env)

    by_key = {target.key: target for target in targets}
    assert by_key["codex"].skills_dir == tmp_path / "codex-skills"
    assert by_key["claude-code"].skills_dir == tmp_path / "claude-skills"


def test_detect_runtime_targets_defaults_to_known_local_dirs(tmp_path: Path) -> None:
    targets = detect_runtime_targets(tmp_path, {})

    by_key = {target.key: target for target in targets}
    assert by_key["codex"].skills_dir == tmp_path / ".codex" / "skills"
    assert by_key["claude-code"].skills_dir == tmp_path / ".claude" / "skills"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_setup.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'ixunfei_docx_reader.setup'`.

- [x] **Step 3: Implement runtime target detection**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class RuntimeTarget:
    key: str
    label: str
    skills_dir: Path
    source_dir: Path


def detect_runtime_targets(home: Path, env: Mapping[str, str]) -> list[RuntimeTarget]:
    codex_dir = Path(env.get("IXFDOC_CODEX_SKILLS_DIR", home / ".codex" / "skills")).expanduser()
    claude_dir = Path(
        env.get("IXFDOC_CLAUDE_CODE_SKILLS_DIR", home / ".claude" / "skills")
    ).expanduser()
    return [
        RuntimeTarget("codex", "Codex", codex_dir, Path("skills/codex/ixunfei-docx-reader")),
        RuntimeTarget(
            "claude-code",
            "Claude Code",
            claude_dir,
            Path("skills/claude-code/ixunfei-docx-reader"),
        ),
    ]
```

- [x] **Step 4: Run detection tests**

Run: `python -m pytest tests/test_setup.py -q`

Expected: PASS.

- [x] **Step 5: Write failing wrapper install tests**

```python
from pathlib import Path

from ixunfei_docx_reader.setup import install_skill_wrappers


def write_wrapper_sources(root: Path) -> None:
    (root / "skills/codex/ixunfei-docx-reader").mkdir(parents=True)
    (root / "skills/claude-code/ixunfei-docx-reader").mkdir(parents=True)
    (root / "skills/codex/ixunfei-docx-reader/SKILL.md").write_text("codex wrapper\n", encoding="utf-8")
    (root / "skills/claude-code/ixunfei-docx-reader/SKILL.md").write_text(
        "claude wrapper\n",
        encoding="utf-8",
    )


def test_install_skill_wrappers_installs_selected_runtime(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write_wrapper_sources(project)
    home = tmp_path / "home"

    payload = install_skill_wrappers(project, home, ["codex"], False, {})

    installed = home / ".codex" / "skills" / "ixunfei-docx-reader" / "SKILL.md"
    assert installed.read_text(encoding="utf-8") == "codex wrapper\n"
    assert payload["installed"][0]["runtime"] == "codex"
    assert not (home / ".claude" / "skills" / "ixunfei-docx-reader").exists()


def test_install_skill_wrappers_refuses_overwrite_without_force(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write_wrapper_sources(project)
    home = tmp_path / "home"
    existing = home / ".codex" / "skills" / "ixunfei-docx-reader"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("user copy\n", encoding="utf-8")

    payload = install_skill_wrappers(project, home, ["codex"], False, {})

    assert existing.joinpath("SKILL.md").read_text(encoding="utf-8") == "user copy\n"
    assert payload["skipped"][0]["reason"] == "exists"
```

- [x] **Step 6: Run wrapper install tests to verify they fail**

Run: `python -m pytest tests/test_setup.py -q`

Expected: FAIL with `ImportError` for `install_skill_wrappers` or assertion failures.

- [x] **Step 7: Implement minimal wrapper installer**

```python
import shutil
from typing import Iterable


def normalize_runtimes(raw: Iterable[str]) -> list[str]:
    values = [item.strip().lower() for item in raw if item.strip()]
    if not values or "auto" in values or "all" in values:
        return ["codex", "claude-code"]
    if "none" in values:
        return []
    out: list[str] = []
    for value in values:
        normalized = value.replace("claude_code", "claude-code").replace("claude", "claude-code")
        if normalized not in {"codex", "claude-code"}:
            raise ValueError(f"unsupported runtime: {value}")
        if normalized not in out:
            out.append(normalized)
    return out


def install_skill_wrappers(
    project_root: Path,
    home: Path,
    runtimes: list[str],
    force: bool,
    env: Mapping[str, str],
) -> dict[str, object]:
    selected = set(normalize_runtimes(runtimes))
    installed: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for target in detect_runtime_targets(home, env):
        if target.key not in selected:
            continue
        source = project_root / target.source_dir
        destination = target.skills_dir / "ixunfei-docx-reader"
        if destination.exists() and not force:
            skipped.append({"runtime": target.key, "path": str(destination), "reason": "exists"})
            continue
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        installed.append({"runtime": target.key, "path": str(destination)})
    return {"ok": True, "installed": installed, "skipped": skipped}
```

- [x] **Step 8: Run setup tests**

Run: `python -m pytest tests/test_setup.py -q`

Expected: PASS.

- [x] **Step 9: Add CLI parser and handler tests**

```python
import json
import subprocess
import sys
from pathlib import Path


def test_setup_skills_json_outputs_machine_readable_status(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ixunfei_docx_reader.cli",
            "setup",
            "skills",
            "--runtimes",
            "none",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["installed"] == []
```

- [x] **Step 10: Run CLI setup test to verify it fails**

Run: `python -m pytest tests/test_cli_contract.py::test_setup_skills_json_outputs_machine_readable_status -q`

Expected: FAIL because `setup` is not a known command.

- [x] **Step 11: Implement `ixfdoc setup skills`**

Add to `build_parser()`:

```python
    setup = subparsers.add_parser("setup", help="Install local agent integration helpers.")
    setup_subparsers = setup.add_subparsers(dest="setup_command")
    setup_subparsers.required = True
    setup_skills = setup_subparsers.add_parser("skills", help="Install Codex/Claude Code skill wrappers.")
    setup_skills.add_argument("--runtimes", default="auto")
    setup_skills.add_argument("--force", action="store_true")
    setup_skills.add_argument("--json", action="store_true", dest="as_json")
```

Add dispatch in `main()`:

```python
    if args.command == "setup" and args.setup_command == "skills":
        return run_setup_skills(args)
```

Add handler:

```python
def run_setup_skills(args: argparse.Namespace) -> int:
    from ixunfei_docx_reader.setup import install_skill_wrappers

    project_root = Path(__file__).resolve().parents[2]
    payload = install_skill_wrappers(
        project_root,
        Path.home(),
        args.runtimes.split(","),
        args.force,
        dict(os.environ),
    )
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"installed {len(payload['installed'])} wrapper(s)")
        if payload["skipped"]:
            print(f"skipped {len(payload['skipped'])} existing wrapper(s); pass --force to overwrite")
    return 0
```

- [x] **Step 12: Run setup and existing tests**

Run: `python -m pytest tests/test_setup.py tests/test_cli_contract.py -q`

Expected: PASS.

- [x] **Step 13: Commit**

```bash
git add src/ixunfei_docx_reader/setup.py src/ixunfei_docx_reader/cli.py tests/test_setup.py tests/test_cli_contract.py
git commit -m "feat: add skill wrapper setup command"
```

---

### Task 2: Add CI Checks

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `pyproject.toml`
- Test: local command execution

**Interfaces:**
- Consumes: existing pytest suite
- Produces: GitHub Actions workflow running tests and compile checks on macOS and Windows

- [x] **Step 1: Add minimal lint dependency**

Modify `pyproject.toml`:

```toml
dev = [
  "pytest>=8.0",
  "ruff>=0.5",
]
```

- [x] **Step 2: Create CI workflow**

```yaml
name: CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    name: Python ${{ matrix.python-version }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [macos-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install package
        run: python -m pip install -e ".[dev]"
      - name: Compile source
        run: python -m compileall -q src
      - name: Run tests
        run: python -m pytest -q
      - name: Ruff check
        run: python -m ruff check .
```

- [x] **Step 3: Run the CI-equivalent commands locally**

Run:

```bash
python -m pip install -e ".[dev]"
python -m compileall -q src
python -m pytest -q
python -m ruff check .
```

Expected: all commands exit 0.

- [x] **Step 4: Commit**

```bash
git add pyproject.toml .github/workflows/ci.yml
git commit -m "ci: add python test workflow"
```

---

### Task 3: Add Release Packaging Workflow

**Files:**
- Create: `.github/workflows/release.yml`
- Create: `docs/release.md`
- Modify: `README.md`
- Test: local build command execution

**Interfaces:**
- Consumes: Python package metadata in `pyproject.toml`
- Produces: GitHub release workflow that builds wheel/sdist on tag push

- [x] **Step 1: Add build dependency to dev extras**

Modify `pyproject.toml`:

```toml
dev = [
  "pytest>=8.0",
  "ruff>=0.5",
  "build>=1.2",
]
```

- [x] **Step 2: Create release workflow**

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install build tools
        run: python -m pip install build
      - name: Build distributions
        run: python -m build
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ixunfei-docx-reader-dist
          path: dist/*
```

- [x] **Step 3: Add release documentation**

```markdown
# Release

`ixunfei-docx-reader` releases are intentionally small Python package builds.

## Local Checks

Run before tagging:

```bash
python -m compileall -q src
python -m pytest -q
python -m build
```

## Tag

```bash
git tag v0.1.0
git push origin v0.1.0
```

The GitHub Actions release workflow builds `sdist` and `wheel` artifacts and uploads them as workflow artifacts.

## Publishing

Do not publish to PyPI until the README, privacy notes, and Windows support status are current.
```

- [x] **Step 4: Link release docs from README**

Add under `Install`:

```markdown
Release build notes live in [`docs/release.md`](docs/release.md).
```

- [x] **Step 5: Run local build checks**

Run:

```bash
python -m pip install -e ".[dev]"
python -m build
python -m pytest -q
```

Expected: build creates `dist/*.whl` and `dist/*.tar.gz`; tests pass.

- [x] **Step 6: Commit**

```bash
git add pyproject.toml .github/workflows/release.yml docs/release.md README.md
git commit -m "ci: add release packaging workflow"
```

---

### Task 4: Add Windows Cookie Provider Skeleton

**Files:**
- Create: `src/ixunfei_docx_reader/cookies/windows_larkshell.py`
- Modify: `src/ixunfei_docx_reader/cli.py`
- Test: `tests/test_windows_cookie_provider.py`
- Test: `tests/test_cli_contract.py`

**Interfaces:**
- Consumes: Chromium cookie DB rows from Windows LarkShell profile
- Produces: `export_cookies(output: Path, app_data: Path | None = None, cookies_db: Path | None = None, host_like: str = DEFAULT_HOST_LIKE) -> dict[str, object]`
- Produces CLI provider: `ixfdoc cookies export --provider windows-larkshell`
- Produces `--provider auto` routing to Windows provider when `platform.system().lower() == "windows"`

- [x] **Step 1: Write failing Windows unsupported-environment tests**

```python
from pathlib import Path

import pytest

from ixunfei_docx_reader.cookies.windows_larkshell import find_cookie_db


def test_find_cookie_db_returns_explicit_path(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    db.write_bytes(b"sqlite")

    assert find_cookie_db(cookies_db=db, app_data=None) == db


def test_find_cookie_db_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Windows LarkShell cookie DB not found"):
        find_cookie_db(cookies_db=None, app_data=tmp_path)
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_windows_cookie_provider.py -q`

Expected: FAIL with `ModuleNotFoundError`.

- [x] **Step 3: Implement provider discovery skeleton**

```python
from __future__ import annotations

from pathlib import Path


DEFAULT_HOST_LIKE = "%xfchat.iflytek.com%"


def find_cookie_db(cookies_db: Path | None, app_data: Path | None) -> Path:
    if cookies_db is not None:
        path = cookies_db.expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"Windows LarkShell cookie DB not found: {path}")
    if app_data is None:
        raise FileNotFoundError("Windows LarkShell cookie DB not found: APPDATA is not set")
    candidates = [
        app_data / "LarkShell" / "User Data" / "Default" / "Network" / "Cookies",
        app_data / "LarkShell" / "User Data" / "Default" / "Cookies",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Windows LarkShell cookie DB not found under APPDATA")
```

- [x] **Step 4: Run skeleton tests**

Run: `python -m pytest tests/test_windows_cookie_provider.py -q`

Expected: PASS.

- [x] **Step 5: Write failing CLI provider test**

```python
import subprocess
import sys


def test_cookies_export_accepts_windows_larkshell_provider() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ixunfei_docx_reader.cli",
            "cookies",
            "export",
            "--provider",
            "windows-larkshell",
            "--cookies-db",
            "/definitely/missing/Cookies",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 6
    assert "Windows LarkShell cookie DB not found" in result.stderr
```

- [x] **Step 6: Run CLI provider test to verify it fails**

Run: `python -m pytest tests/test_cli_contract.py::test_cookies_export_accepts_windows_larkshell_provider -q`

Expected: FAIL because argparse rejects `windows-larkshell`.

- [x] **Step 7: Wire provider into CLI without full DPAPI yet**

Modify imports:

```python
from ixunfei_docx_reader.cookies.windows_larkshell import (
    export_cookies as export_windows_larkshell_cookies,
)
```

Modify provider choices:

```python
export.add_argument("--provider", default="auto", choices=["auto", "macos-larkshell", "windows-larkshell"])
```

Modify `run_cookie_export` routing:

```python
    provider = args.provider
    if provider == "auto":
        provider = "windows-larkshell" if platform_name() == "windows" else "macos-larkshell"
    if provider == "windows-larkshell":
        try:
            payload = export_windows_larkshell_cookies(
                output=Path(args.output).expanduser(),
                cookies_db=Path(args.cookies_db).expanduser() if args.cookies_db else None,
            )
        except Exception as exc:
            fail(
                error_type="cookie",
                subtype="cookie_export_failed",
                message=str(exc),
                hint="Open i讯飞/LarkShell desktop on Windows, confirm you are logged in, then retry.",
                retryable=True,
            )
        print(json.dumps(payload, ensure_ascii=False))
        return 0
```

Add temporary provider implementation:

```python
def export_cookies(output: Path, app_data: Path | None = None, cookies_db: Path | None = None, host_like: str = DEFAULT_HOST_LIKE) -> dict[str, object]:
    find_cookie_db(cookies_db=cookies_db, app_data=app_data)
    raise RuntimeError("Windows cookie decryption is not implemented yet.")
```

- [x] **Step 8: Run provider tests**

Run:

```bash
python -m pytest tests/test_windows_cookie_provider.py tests/test_cli_contract.py -q
```

Expected: PASS.

- [x] **Step 9: Commit**

```bash
git add src/ixunfei_docx_reader/cookies/windows_larkshell.py src/ixunfei_docx_reader/cli.py tests/test_windows_cookie_provider.py tests/test_cli_contract.py
git commit -m "feat: add windows cookie provider skeleton"
```

---

### Task 5: Implement Windows DPAPI Cookie Export

**Files:**
- Modify: `src/ixunfei_docx_reader/cookies/windows_larkshell.py`
- Modify: `pyproject.toml`
- Test: `tests/test_windows_cookie_provider.py`
- Docs: `docs/supported-platforms.md`

**Interfaces:**
- Consumes: Windows Chromium `encrypted_value` bytes and Local State encrypted key
- Produces: JSON browser cookie objects compatible with existing `load_cookie_objects`
- Produces optional dependency group: `windows = ["pywin32>=306"]`

- [x] **Step 1: Add Windows optional dependency**

Modify `pyproject.toml`:

```toml
windows = [
  "pywin32>=306; platform_system == 'Windows'",
]
```

- [x] **Step 2: Write unit tests for injectable decryptor**

```python
from pathlib import Path

from ixunfei_docx_reader.cookies.windows_larkshell import row_to_cookie


def test_row_to_cookie_uses_plain_value_when_present() -> None:
    row = {
        "host_key": ".xfchat.iflytek.com",
        "name": "_csrf_token",
        "value": "plain",
        "encrypted_value": b"",
        "path": "/",
        "is_secure": 1,
    }

    cookie = row_to_cookie(row, decrypt_value=lambda value: "decrypted")

    assert cookie["value"] == "plain"
    assert cookie["secure"] is True


def test_row_to_cookie_decrypts_encrypted_value() -> None:
    row = {
        "host_key": ".xfchat.iflytek.com",
        "name": "session",
        "value": "",
        "encrypted_value": b"encrypted",
        "path": "/",
        "is_secure": 0,
    }

    cookie = row_to_cookie(row, decrypt_value=lambda value: "secret")

    assert cookie["value"] == "secret"
    assert cookie["secure"] is False
```

- [x] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_windows_cookie_provider.py -q`

Expected: FAIL because `row_to_cookie` does not exist.

- [x] **Step 4: Implement row conversion**

```python
from collections.abc import Callable
from typing import Any


def row_to_cookie(row: dict[str, Any], decrypt_value: Callable[[bytes], str]) -> dict[str, object]:
    value = str(row.get("value") or "")
    encrypted = row.get("encrypted_value") or b""
    if not value and encrypted:
        value = decrypt_value(bytes(encrypted))
    return {
        "domain": str(row["host_key"]),
        "name": str(row["name"]),
        "value": value,
        "path": str(row.get("path") or "/"),
        "secure": bool(row.get("is_secure")),
    }
```

- [x] **Step 5: Add SQLite export test with injected decryptor**

```python
import sqlite3
from pathlib import Path

from ixunfei_docx_reader.cookies.windows_larkshell import export_cookies_from_db


def test_export_cookies_from_db_writes_browser_cookie_json(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE cookies (host_key TEXT, name TEXT, value TEXT, encrypted_value BLOB, path TEXT, is_secure INTEGER)"
    )
    conn.execute(
        "INSERT INTO cookies VALUES (?, ?, ?, ?, ?, ?)",
        (".xfchat.iflytek.com", "_csrf_token", "", b"encrypted", "/", 1),
    )
    conn.commit()
    conn.close()
    output = tmp_path / "cookies.json"

    payload = export_cookies_from_db(
        db,
        output,
        "%xfchat.iflytek.com%",
        decrypt_value=lambda value: "csrf",
    )

    assert payload["cookieCount"] == 1
    assert payload["hasCsrf"] is True
    assert output.read_text(encoding="utf-8").count("csrf") == 1
```

- [x] **Step 6: Run export test to verify it fails**

Run: `python -m pytest tests/test_windows_cookie_provider.py::test_export_cookies_from_db_writes_browser_cookie_json -q`

Expected: FAIL because `export_cookies_from_db` does not exist.

- [x] **Step 7: Implement SQLite export with file permissions**

```python
import json
import os
import sqlite3


def export_cookies_from_db(
    db_path: Path,
    output: Path,
    host_like: str,
    decrypt_value: Callable[[bytes], str],
) -> dict[str, object]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT host_key, name, value, encrypted_value, path, is_secure
            FROM cookies
            WHERE host_key LIKE ?
            ORDER BY host_key, name
            """,
            (host_like,),
        ).fetchall()
    finally:
        conn.close()
    cookies = [row_to_cookie(dict(row), decrypt_value) for row in rows]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(output, 0o600)
    except OSError:
        pass
    return {
        "ok": True,
        "provider": "windows-larkshell",
        "output": str(output),
        "cookieCount": len(cookies),
        "hasCsrf": any(cookie["name"] == "_csrf_token" for cookie in cookies),
    }
```

- [x] **Step 8: Implement DPAPI decryptor**

```python
def decrypt_dpapi_value(encrypted_value: bytes) -> str:
    try:
        import win32crypt
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is required on Windows. Install with `python -m pip install -e \".[windows]\"`."
        ) from exc
    _, decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)
    return decrypted.decode("utf-8")
```

Update `export_cookies`:

```python
def export_cookies(
    output: Path,
    app_data: Path | None = None,
    cookies_db: Path | None = None,
    host_like: str = DEFAULT_HOST_LIKE,
) -> dict[str, object]:
    db_path = find_cookie_db(cookies_db=cookies_db, app_data=app_data)
    return export_cookies_from_db(db_path, output, host_like, decrypt_dpapi_value)
```

- [x] **Step 9: Run provider tests**

Run: `python -m pytest tests/test_windows_cookie_provider.py -q`

Expected: PASS.

- [x] **Step 10: Update platform docs**

Add to `docs/supported-platforms.md`:

```markdown
## Windows

Windows support uses the local LarkShell Chromium cookie database and DPAPI through `pywin32`.

Install with:

```bash
python -m pip install -e ".[windows]"
ixfdoc cookies export --provider windows-larkshell --output %TEMP%\\ixunfei_profile_explorer_cookies.json
ixfdoc doctor --json --cookies %TEMP%\\ixunfei_profile_explorer_cookies.json
```

Do not use this on Linux; i讯飞 does not ship a Linux desktop client.
```

- [x] **Step 11: Run full verification**

Run:

```bash
python -m compileall -q src
python -m pytest -q
```

Expected: PASS.

- [x] **Step 12: Commit**

```bash
git add pyproject.toml src/ixunfei_docx_reader/cookies/windows_larkshell.py tests/test_windows_cookie_provider.py docs/supported-platforms.md
git commit -m "feat: support windows larkshell cookie export"
```

---

### Task 6: Tighten README and Public Positioning

**Files:**
- Modify: `README.md`
- Modify: `PRIVACY.md`
- Modify: `SECURITY.md`
- Modify: `docs/supported-platforms.md`
- Test: manual doc review plus command smoke tests

**Interfaces:**
- Consumes: CLI commands from Tasks 1-5
- Produces: public-facing README that explains CLI-first architecture, supported platforms, Codex/Claude Code installation, and privacy boundaries

- [x] **Step 1: Rewrite README positioning section**

Use this concise opening:

```markdown
# ixunfei-docx-reader

Read authorized i讯飞/LarkShell private documents into local Markdown/TSV files for agent analysis.

`ixunfei-docx-reader` is a small CLI-first project:

- `ixfdoc` is the source of truth.
- Codex and Claude Code skills are thin wrappers around `ixfdoc`.
- Document content stays local unless you choose to send generated files elsewhere.
- Cookie export uses your local desktop login session and never prints cookie values.
```

- [x] **Step 2: Add install section**

```markdown
## Install

For development:

```bash
python -m pip install -e ".[crypto,dev]"
ixfdoc --version
```

For Windows cookie export:

```bash
python -m pip install -e ".[windows]"
```
```

- [x] **Step 3: Add skill wrapper setup section**

```markdown
## Agent Wrappers

Install local wrappers for Codex and Claude Code:

```bash
ixfdoc setup skills --runtimes auto --json
```

The wrappers do not parse documents. They call `ixfdoc read`, parse the CLI JSON error contract, and follow the returned hint.
```

- [x] **Step 4: Add privacy warning**

```markdown
## Privacy

Treat exported cookies and generated Markdown/TSV as sensitive. Do not commit them. Do not paste cookie values into issues, logs, or prompts.
```

- [x] **Step 5: Run docs command smoke tests**

Run:

```bash
ixfdoc --version
ixfdoc doctor --json
ixfdoc setup skills --runtimes none --json
```

Expected: each command exits 0 and prints no cookie values.

- [x] **Step 6: Commit**

```bash
git add README.md PRIVACY.md SECURITY.md docs/supported-platforms.md
git commit -m "docs: clarify cli-first public positioning"
```

---

### Task 7: Add End-to-End Smoke Script for Maintainers

**Files:**
- Create: `scripts/smoke.sh`
- Create: `scripts/smoke.ps1`
- Modify: `README.md`
- Test: local smoke command execution

**Interfaces:**
- Consumes: installed editable package
- Produces: maintainers can run one smoke command before release

- [x] **Step 1: Create POSIX smoke script**

```sh
#!/bin/sh
set -eu

python -m compileall -q src
python -m pytest -q
ixfdoc --version
ixfdoc doctor --json >/dev/null
ixfdoc setup skills --runtimes none --json >/dev/null
```

- [x] **Step 2: Create PowerShell smoke script**

```powershell
$ErrorActionPreference = "Stop"

python -m compileall -q src
python -m pytest -q
ixfdoc --version
ixfdoc doctor --json | Out-Null
ixfdoc setup skills --runtimes none --json | Out-Null
```

- [x] **Step 3: Mark POSIX smoke script executable**

Run: `chmod +x scripts/smoke.sh`

Expected: command exits 0.

- [x] **Step 4: Run POSIX smoke script**

Run: `scripts/smoke.sh`

Expected: command exits 0.

- [x] **Step 5: Document smoke scripts**

Add to `README.md`:

```markdown
## Maintainer Smoke Test

```bash
scripts/smoke.sh
```

On Windows:

```powershell
scripts\\smoke.ps1
```
```

- [x] **Step 6: Commit**

```bash
git add scripts/smoke.sh scripts/smoke.ps1 README.md
git commit -m "test: add maintainer smoke scripts"
```

---

## Execution Order

1. Task 1: add `ixfdoc setup skills`, because it makes Codex/Claude Code usage concrete without changing reader behavior.
2. Task 2: add CI, because every later provider and packaging change needs automated verification.
3. Task 3: add release packaging, because public users need installable artifacts before broad promotion.
4. Task 4: add Windows provider skeleton, because it creates the CLI/API boundary safely before DPAPI details.
5. Task 5: implement Windows export, because this is the largest platform feature and should happen after CI exists.
6. Task 6: tighten public docs after the actual behavior exists.
7. Task 7: add maintainer smoke scripts once the command surface is stable.

## Deferred On Purpose

- `curl | bash` installer: defer until PyPI/GitHub Release behavior is stable.
- Auto-update: not needed for a document reader.
- GUI/browser extension: not needed and increases security surface.
- Multi-skill framework: unnecessary; this project has one core capability.
- Linux support: intentionally excluded because there is no i讯飞 Linux desktop client.
- Rich full-fidelity Markdown styling: useful later, but not blocking engineering hardening.
- GFM table rendering: useful later, but not required for installability or platform support.

## Completion Criteria

- `ixfdoc --version` works from an editable install.
- `ixfdoc setup skills --runtimes none --json` returns valid JSON.
- `ixfdoc setup skills --runtimes auto --json` can install/update local Codex and Claude Code wrappers.
- `python -m pytest -q` passes.
- `python -m compileall -q src` passes.
- GitHub Actions CI is present.
- README states clearly that the project is a CLI/Python package with optional thin skill wrappers.
- Docs mention macOS and Windows only; no Linux support claim remains.
- Cookie values are never printed by docs, CLI diagnostics, tests, or errors.

## Self-Review

- Spec coverage: The plan covers CLI-first architecture, thin Codex/Claude Code wrappers, macOS/Windows platform positioning, setup/install flow, CI, release packaging, and Windows cookie provider work.
- Placeholder scan: No `TBD`, `TODO`, or unspecified edge-case placeholders remain.
- Type consistency: `RuntimeTarget`, `detect_runtime_targets`, `install_skill_wrappers`, `find_cookie_db`, `row_to_cookie`, and `export_cookies_from_db` are defined before later tasks consume them.
- Simplicity check: The plan intentionally excludes daemon/background services, browser extensions, auto-update, marketplace-scale plugin handling, and Linux support.
