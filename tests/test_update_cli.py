import json
from pathlib import Path

import pytest
import requests

from ixunfei_docx_reader import cli


def test_update_check_json_reports_available_release(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_get_latest_release(repo: str) -> dict[str, object]:
        assert repo == "owner/project"
        return {
            "tag_name": "v0.1.7",
            "html_url": "https://github.com/owner/project/releases/tag/v0.1.7",
        }

    monkeypatch.setattr(cli, "get_latest_github_release", fake_get_latest_release)

    exit_code = cli.main(["update", "check", "--repo", "owner/project", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["currentVersion"] == cli.__version__
    assert payload["latestVersion"] == "0.1.7"
    assert payload["latestTag"] == "v0.1.7"
    assert payload["updateAvailable"] is True
    assert payload["releaseUrl"] == "https://github.com/owner/project/releases/tag/v0.1.7"
    assert "pip install --upgrade" in payload["installCommand"]


def test_update_check_json_reports_current_when_latest_matches(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_get_latest_release(repo: str) -> dict[str, object]:
        assert repo == "serialq7ic4/ixunfei-docx-reader"
        return {
            "tag_name": f"v{cli.__version__}",
            "html_url": "https://github.com/serialq7ic4/ixunfei-docx-reader/releases/latest",
        }

    monkeypatch.setattr(cli, "get_latest_github_release", fake_get_latest_release)

    exit_code = cli.main(["update", "check", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["latestVersion"] == cli.__version__
    assert payload["updateAvailable"] is False
    assert payload["installCommand"] == ""


def test_update_check_network_failure_returns_json_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_get_latest_release(repo: str) -> dict[str, object]:
        raise requests.RequestException("network unavailable")

    monkeypatch.setattr(cli, "get_latest_github_release", fake_get_latest_release)

    with pytest.raises(SystemExit) as exc:
        cli.main(["update", "check", "--json"])

    assert exc.value.code == 10
    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["error"]["type"] == "remote"
    assert payload["error"]["subtype"] == "update_check_failed"
    assert payload["error"]["retryable"] is True


def test_update_skills_force_refreshes_packaged_wrappers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fake_install_skill_wrappers(
        project_root: Path,
        home: Path,
        runtimes: list[str],
        force: bool,
        env: dict[str, str],
    ) -> dict[str, object]:
        calls.append(
            {
                "project_root": project_root,
                "home": home,
                "runtimes": runtimes,
                "force": force,
                "env": env,
            }
        )
        return {"ok": True, "installed": [{"runtime": "codex", "path": "/tmp/skill"}], "skipped": []}

    monkeypatch.setattr(cli, "install_packaged_skill_wrappers", fake_install_skill_wrappers)
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)

    exit_code = cli.main(["update", "skills", "--runtimes", "codex", "--json"])

    assert exit_code == 0
    assert calls
    assert calls[0]["runtimes"] == ["codex"]
    assert calls[0]["force"] is True
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["updated"] is True
    assert payload["installed"] == [{"runtime": "codex", "path": "/tmp/skill"}]


def test_update_skills_invalid_runtime_returns_json_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_install_skill_wrappers(
        project_root: Path,
        home: Path,
        runtimes: list[str],
        force: bool,
        env: dict[str, str],
    ) -> dict[str, object]:
        raise ValueError("unsupported runtime: vim")

    monkeypatch.setattr(cli, "install_packaged_skill_wrappers", fake_install_skill_wrappers)

    with pytest.raises(SystemExit) as exc:
        cli.main(["update", "skills", "--runtimes", "vim", "--json"])

    assert exc.value.code == 2
    payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["error"]["type"] == "usage"
    assert payload["error"]["subtype"] == "bad_args"
    assert "unsupported runtime: vim" in payload["error"]["message"]
