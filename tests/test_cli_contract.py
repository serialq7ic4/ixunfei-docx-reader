import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TEST_ENV = {
    **os.environ,
    "PYTHONPATH": str(ROOT / "src"),
}


def run_module(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ixunfei_docx_reader.cli", *args],
        cwd=ROOT,
        env=TEST_ENV,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_reports_version() -> None:
    result = run_module("--version")

    assert result.returncode == 0
    assert "ixfdoc" in result.stdout


def test_bad_args_end_stderr_with_json_error() -> None:
    result = run_module("read")

    assert result.returncode == 2
    last_line = result.stderr.strip().splitlines()[-1]
    payload = json.loads(last_line)
    assert payload == {
        "ok": False,
        "error": {
            "type": "usage",
            "subtype": "bad_args",
            "message": "read requires at least one source.",
            "hint": "Run `ixfdoc read <url-or-file>... --out-dir <dir>`.",
            "retryable": False,
        },
    }


def test_doctor_json_reports_basic_runtime() -> None:
    result = run_module("doctor", "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["cli"] == "ixfdoc"
    assert payload["platform"] in {"macos", "windows", "other"}


def test_setup_skills_json_outputs_machine_readable_status() -> None:
    result = run_module("setup", "skills", "--runtimes", "none", "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["installed"] == []


def test_setup_skills_invalid_runtime_returns_json_error() -> None:
    result = run_module("setup", "skills", "--runtimes", "vim", "--json")

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["error"]["type"] == "usage"
    assert payload["error"]["subtype"] == "bad_args"
    assert "unsupported runtime: vim" in payload["error"]["message"]


def test_setup_skills_invalid_runtime_without_json_returns_json_error() -> None:
    result = run_module("setup", "skills", "--runtimes", "vim")

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["error"]["type"] == "usage"
    assert payload["error"]["subtype"] == "bad_args"
    assert "unsupported runtime: vim" in payload["error"]["message"]


def test_doctor_json_reports_cookie_metadata_without_values(tmp_path: Path) -> None:
    cookies_path = tmp_path / "cookies.json"
    cookies_path.write_text(
        json.dumps(
            [
                {
                    "name": "_csrf_token",
                    "value": "secret-csrf",
                    "domain": ".xfchat.iflytek.com",
                    "path": "/",
                },
                {
                    "name": "session",
                    "value": "secret-session",
                    "domain": ".xfchat.iflytek.com",
                    "path": "/",
                },
            ]
        ),
        encoding="utf-8",
    )

    result = run_module("doctor", "--json", "--cookies", str(cookies_path))

    assert result.returncode == 0
    assert "secret-csrf" not in result.stdout
    assert "secret-session" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload["cookies"] == {
        "path": str(cookies_path),
        "exists": True,
        "readable": True,
        "cookieCount": 2,
        "hasCsrf": True,
    }


def test_inspect_local_markdown_reports_safe_summary(tmp_path: Path) -> None:
    source = tmp_path / "private-source.md"
    source.write_text("# Secret Title\n\nSensitive body should not appear.\n", encoding="utf-8")

    result = run_module("inspect", str(source), "--json")

    assert result.returncode == 0
    assert "Secret Title" not in result.stdout
    assert "Sensitive body" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "ok": True,
        "source": str(source),
        "remote": False,
        "kind": "local_markdown",
        "path": str(source),
        "exists": True,
        "readable": True,
        "sizeBytes": source.stat().st_size,
        "suffix": ".md",
    }


def test_inspect_docx_url_reports_safe_route_summary() -> None:
    source = "https://tenant.xfchat.iflytek.com/docx/doxfixturetoken?from=copy"

    result = run_module("inspect", source, "--json")

    assert result.returncode == 0
    assert "doxfixturetoken" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "ok": True,
        "sourceRef": "https://tenant.xfchat.iflytek.com/docx/<redacted>?from=copy",
        "remote": True,
        "kind": "docx",
        "host": "tenant.xfchat.iflytek.com",
        "pathType": "docx",
        "tokenPrefix": "dox",
        "tokenLength": len("doxfixturetoken"),
        "route": "docx_client_vars",
    }


def test_inspect_okr_url_reports_safe_route_summary() -> None:
    owner_id = "1000000000000000000"
    okr_id = "2000000000000000000"
    source = (
        f"https://tenant.xfchat.iflytek.com/okr/user/{owner_id}/"
        f"?lang=zh-CN&okrId={okr_id}&open_in_browser=true&type=my"
    )

    result = run_module("inspect", source, "--json")

    assert result.returncode == 0
    assert owner_id not in result.stdout
    assert okr_id not in result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "ok": True,
        "sourceRef": (
            "https://tenant.xfchat.iflytek.com/okr/user/<redacted>/"
            "?lang=zh-CN&okrId=<redacted>&open_in_browser=true&type=my"
        ),
        "remote": True,
        "kind": "okr",
        "host": "tenant.xfchat.iflytek.com",
        "pathType": "okr",
        "tokenPrefix": "200",
        "tokenLength": len(okr_id),
        "route": "okr_detail",
    }


def test_inspect_missing_local_file_returns_json_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.md"

    result = run_module("inspect", str(missing), "--json")

    assert result.returncode == 2
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload == {
        "ok": False,
        "error": {
            "type": "usage",
            "subtype": "bad_args",
            "message": f"local file not found: {missing}",
            "hint": "Pass an existing local path or a supported i讯飞 document URL.",
            "retryable": False,
        },
    }


def test_read_local_markdown_writes_output_and_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Source\n\nHello from local file.\n", encoding="utf-8")
    out_dir = tmp_path / "out"

    result = run_module("read", str(source), "--out-dir", str(out_dir), "--print-manifest")

    assert result.returncode == 0
    manifest = json.loads(result.stdout)
    item = manifest["local_markdown_1"]
    output_path = Path(item["file"])
    assert item["kind"] == "local_markdown"
    assert item["title"] == "source.md"
    assert output_path.read_text(encoding="utf-8") == "# Source\n\nHello from local file.\n"
    assert (out_dir / "manifest.json").exists()


def test_read_multiple_local_markdown_outputs_use_source_stems(tmp_path: Path) -> None:
    source_a = tmp_path / "Project Plan.md"
    source_b = tmp_path / "project-plan.md"
    source_a.write_text("# A\n", encoding="utf-8")
    source_b.write_text("# B\n", encoding="utf-8")
    out_dir = tmp_path / "out"

    result = run_module(
        "read",
        str(source_a),
        str(source_b),
        "--out-dir",
        str(out_dir),
        "--print-manifest",
    )

    assert result.returncode == 0
    manifest = json.loads(result.stdout)
    item_a = manifest["local_markdown_1"]
    item_b = manifest["local_markdown_2"]
    assert item_a["file"] == str(out_dir / "project-plan.md")
    assert item_b["file"] == str(out_dir / "project-plan-2.md")
    assert Path(item_a["file"]).read_text(encoding="utf-8") == "# A\n"
    assert Path(item_b["file"]).read_text(encoding="utf-8") == "# B\n"


def test_read_local_markdown_cleanup_removes_output_dir_after_manifest_print(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Source\n\nSensitive local content.\n", encoding="utf-8")
    out_dir = tmp_path / "out"

    result = run_module(
        "read",
        str(source),
        "--out-dir",
        str(out_dir),
        "--print-manifest",
        "--cleanup",
    )

    assert result.returncode == 0
    manifest = json.loads(result.stdout)
    item = manifest["local_markdown_1"]
    assert item["kind"] == "local_markdown"
    assert item["file"] == str(out_dir / "source.md")
    assert not out_dir.exists()


def test_read_cleanup_preserves_unrelated_files_in_output_dir(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Source\n\nSensitive local content.\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    keep = out_dir / "keep.txt"
    keep.write_text("do not delete\n", encoding="utf-8")

    result = run_module(
        "read",
        str(source),
        "--out-dir",
        str(out_dir),
        "--cleanup",
    )

    assert result.returncode == 0
    assert keep.read_text(encoding="utf-8") == "do not delete\n"
    assert out_dir.exists()
    assert not (out_dir / "local-markdown-1.md").exists()
    assert not (out_dir / "manifest.json").exists()


def test_read_remote_missing_cookie_file_ends_stderr_with_json_error(tmp_path: Path) -> None:
    missing_cookie = tmp_path / "missing-cookies.json"

    result = run_module(
        "read",
        "https://example.com/docx/doxfixturetoken",
        "--cookies",
        str(missing_cookie),
    )

    assert result.returncode == 5
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload == {
        "ok": False,
        "error": {
            "type": "cookie",
            "subtype": "cookie_file_missing",
            "message": f"Cookie file not found: {missing_cookie}",
            "hint": "Run `ixfdoc cookies export --provider auto --output <path>` or pass --cookies.",
            "retryable": False,
        },
    }


def test_read_remote_invalid_cookie_file_ends_stderr_with_json_error(tmp_path: Path) -> None:
    bad_cookie = tmp_path / "bad-cookies.json"
    bad_cookie.write_text('{"not": "a browser cookie list"}', encoding="utf-8")

    result = run_module(
        "read",
        "https://example.com/docx/doxfixturetoken",
        "--cookies",
        str(bad_cookie),
    )

    assert result.returncode == 7
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload == {
        "ok": False,
        "error": {
            "type": "cookie",
            "subtype": "cookie_file_invalid",
            "message": "Cookie JSON must be a list of browser cookie objects.",
            "hint": "Run `ixfdoc cookies export --provider auto --output <path>` or pass a valid --cookies file.",
            "retryable": False,
        },
    }


def test_read_remote_cookie_without_csrf_ends_stderr_with_json_error(tmp_path: Path) -> None:
    cookies_path = tmp_path / "cookies-without-csrf.json"
    cookies_path.write_text(
        json.dumps(
            [
                {
                    "name": "session",
                    "value": "session-fixture",
                    "domain": ".xfchat.iflytek.com",
                    "path": "/",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_module(
        "read",
        "https://example.com/docx/doxfixturetoken",
        "--cookies",
        str(cookies_path),
    )

    assert result.returncode == 8
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload == {
        "ok": False,
        "error": {
            "type": "cookie",
            "subtype": "cookie_csrf_missing",
            "message": "Cookie jar does not contain _csrf_token.",
            "hint": "Run `ixfdoc cookies export --provider auto --output <path>` to refresh the local desktop session cookies.",
            "retryable": False,
        },
    }


def test_read_remote_network_failure_ends_stderr_with_json_error(tmp_path: Path) -> None:
    cookies_path = tmp_path / "cookies.json"
    cookies_path.write_text(
        json.dumps(
            [
                {
                    "name": "_csrf_token",
                    "value": "csrf-fixture",
                    "domain": "127.0.0.1",
                    "path": "/",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_module(
        "read",
        "http://127.0.0.1:9/docx/doxfixturetoken",
        "--cookies",
        str(cookies_path),
    )

    assert result.returncode == 9
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["error"]["type"] == "remote"
    assert payload["error"]["subtype"] == "remote_read_failed"
    assert payload["error"]["retryable"] is True


def test_cookies_export_from_explicit_sqlite_db(tmp_path: Path) -> None:
    cookies_db = tmp_path / "Cookies"
    output = tmp_path / "cookies.json"
    con = sqlite3.connect(cookies_db)
    con.execute(
        """
        create table cookies (
            host_key text,
            name text,
            value text,
            encrypted_value blob,
            path text,
            expires_utc integer,
            is_secure integer,
            is_httponly integer,
            samesite integer
        )
        """
    )
    con.executemany(
        """
        insert into cookies
        (host_key, name, value, encrypted_value, path, expires_utc, is_secure, is_httponly, samesite)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                ".xfchat.iflytek.com",
                "_csrf_token",
                "csrf-fixture",
                b"",
                "/",
                0,
                1,
                1,
                0,
            ),
            (
                ".xfchat.iflytek.com",
                "session",
                "session-fixture",
                b"",
                "/",
                0,
                1,
                1,
                0,
            ),
        ],
    )
    con.commit()
    con.close()

    result = run_module(
        "cookies",
        "export",
        "--provider",
        "macos-larkshell",
        "--cookies-db",
        str(cookies_db),
        "--output",
        str(output),
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["hasCsrf"] is True
    assert payload["cookieCount"] == 2
    assert payload["output"] == str(output)
    cookies = json.loads(output.read_text(encoding="utf-8"))
    assert [cookie["name"] for cookie in cookies] == ["_csrf_token", "session"]


def test_cookies_export_missing_db_ends_stderr_with_json_error(tmp_path: Path) -> None:
    missing_db = tmp_path / "missing-Cookies"

    result = run_module(
        "cookies",
        "export",
        "--provider",
        "macos-larkshell",
        "--cookies-db",
        str(missing_db),
        "--output",
        str(tmp_path / "cookies.json"),
    )

    assert result.returncode == 6
    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["error"]["type"] == "cookie"
    assert payload["error"]["subtype"] == "cookie_export_failed"
    assert payload["error"]["retryable"] is True


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


def test_cookies_export_auto_routes_to_windows_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ixunfei_docx_reader import cli

    output = tmp_path / "cookies.json"
    calls: list[dict[str, object]] = []

    def fake_export_windows_larkshell_cookies(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"ok": True, "provider": "windows-larkshell", "output": str(output)}

    monkeypatch.setattr(cli.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        cli,
        "export_windows_larkshell_cookies",
        fake_export_windows_larkshell_cookies,
    )

    exit_code = cli.main(["cookies", "export", "--provider", "auto", "--output", str(output)])

    assert exit_code == 0
    assert calls == [
        {"output": output, "cookies_db": None, "host_like": "%xfchat.iflytek.com%"}
    ]
    assert json.loads(capsys.readouterr().out)["provider"] == "windows-larkshell"
