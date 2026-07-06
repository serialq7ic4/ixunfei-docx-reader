from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


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
