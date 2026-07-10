#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def extract_release_notes(changelog: str, tag: str) -> str:
    normalized_tag = tag if tag.startswith("v") else f"v{tag}"
    lines = changelog.splitlines()
    heading_prefix = f"## {normalized_tag} - "

    start = next(
        (index for index, line in enumerate(lines) if line.startswith(heading_prefix)),
        None,
    )
    if start is None:
        raise ValueError(f"release notes not found for {normalized_tag}")

    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    body = "\n".join(lines[start + 1 : end]).strip()
    if not body:
        raise ValueError(f"release notes not found for {normalized_tag}")
    return f"{body}\n"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: extract-release-notes.py <tag>", file=sys.stderr)
        return 2

    try:
        notes = extract_release_notes(
            (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
            args[0],
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    sys.stdout.write(notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
