from pathlib import Path
import subprocess
import sys

from ixunfei_docx_reader.setup import (
    detect_runtime_targets,
    install_skill_wrappers,
    packaged_project_root,
)


def write_wrapper_sources(root: Path) -> None:
    (root / "skills/codex/ixunfei-docx-reader").mkdir(parents=True)
    (root / "skills/claude-code/ixunfei-docx-reader").mkdir(parents=True)
    (root / "skills/codex/ixunfei-docx-reader/SKILL.md").write_text(
        "codex wrapper\n",
        encoding="utf-8",
    )
    (root / "skills/claude-code/ixunfei-docx-reader/SKILL.md").write_text(
        "claude wrapper\n",
        encoding="utf-8",
    )


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


def test_install_skill_wrappers_can_use_packaged_wrapper_sources(tmp_path: Path) -> None:
    home = tmp_path / "home"

    payload = install_skill_wrappers(packaged_project_root(), home, ["codex"], False, {})

    installed = home / ".codex" / "skills" / "ixunfei-docx-reader" / "SKILL.md"
    assert installed.exists()
    assert "ixfdoc read" in installed.read_text(encoding="utf-8")
    assert payload["installed"][0]["runtime"] == "codex"


def test_built_wheel_setup_skills_can_install_packaged_codex_wrapper(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=True,
    )
    wheel = next(dist_dir.glob("*.whl"))
    venv = tmp_path / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv)],
        text=True,
        capture_output=True,
        check=True,
    )
    python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    home = tmp_path / "home"
    codex_skills = home / ".codex" / "skills"
    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "IXFDOC_CODEX_SKILLS_DIR": str(codex_skills),
    }
    subprocess.run(
        [str(python), "-m", "pip", "install", str(wheel)],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    result = subprocess.run(
        [
            str(python),
            "-m",
            "ixunfei_docx_reader.cli",
            "setup",
            "skills",
            "--runtimes",
            "codex",
            "--json",
        ],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
    installed = codex_skills / "ixunfei-docx-reader" / "SKILL.md"
    assert installed.exists()
    assert "ixfdoc read" in installed.read_text(encoding="utf-8")
