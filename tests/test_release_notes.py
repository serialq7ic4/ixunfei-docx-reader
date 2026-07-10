from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract-release-notes.py"


def test_extract_release_notes_returns_only_requested_changelog_body() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "v0.1.6"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("### Added\n")
    assert "### Security" in result.stdout
    assert "## v0.1.6" not in result.stdout
    assert "## v0.1.5" not in result.stdout


def test_extract_release_notes_fails_for_unknown_tag() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "v9.9.9"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "release notes not found for v9.9.9" in result.stderr
