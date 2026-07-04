import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_module(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ixunfei_docx_reader.cli", *args],
        cwd=ROOT,
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
