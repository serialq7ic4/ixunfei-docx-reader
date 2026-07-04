from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from pathlib import Path
from typing import NoReturn

from ixunfei_docx_reader import __version__
from ixunfei_docx_reader.reader import DEFAULT_COOKIES, DEFAULT_SPACE_API, read_sources


EXIT_CODES = {
    "bad_args": 2,
    "cookie_file_missing": 5,
}


def platform_name() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "other"


def fail(
    *,
    error_type: str,
    subtype: str,
    message: str,
    hint: str,
    retryable: bool = False,
) -> NoReturn:
    print(f"ERROR {message}", file=sys.stderr)
    if hint:
        print(f"HINT {hint}", file=sys.stderr)
    print(
        json.dumps(
            {
                "ok": False,
                "error": {
                    "type": error_type,
                    "subtype": subtype,
                    "message": message,
                    "hint": hint,
                    "retryable": retryable,
                },
            },
            ensure_ascii=False,
            separators=(",", ": "),
        ),
        file=sys.stderr,
    )
    raise SystemExit(EXIT_CODES.get(subtype, 1))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ixfdoc")
    parser.add_argument("--version", action="store_true", help="Show version and exit.")
    subparsers = parser.add_subparsers(dest="command")

    read = subparsers.add_parser("read", help="Read documents into Markdown/TSV artifacts.")
    read.add_argument("sources", nargs="*")
    read.add_argument("--out-dir", default="")
    read.add_argument("--expand-sheets", action="store_true")
    read.add_argument("--print-manifest", action="store_true")
    read.add_argument("--cookies", default=DEFAULT_COOKIES)
    read.add_argument("--space-api", default=DEFAULT_SPACE_API)

    doctor = subparsers.add_parser("doctor", help="Print local diagnostic information.")
    doctor.add_argument("--json", action="store_true", dest="as_json")

    return parser


def run_read(args: argparse.Namespace) -> int:
    if not args.sources:
        fail(
            error_type="usage",
            subtype="bad_args",
            message="read requires at least one source.",
            hint="Run `ixfdoc read <url-or-file>... --out-dir <dir>`.",
        )
    try:
        results = read_sources(
            args.sources,
            cookies_path=Path(args.cookies).expanduser(),
            space_api=args.space_api,
            expand_sheets=args.expand_sheets,
        )
    except FileNotFoundError as exc:
        message = str(exc)
        if message.startswith("Cookie file not found:"):
            fail(
                error_type="cookie",
                subtype="cookie_file_missing",
                message=message,
                hint="Run `ixfdoc cookies export --provider auto --output <path>` or pass --cookies.",
            )
        fail(
            error_type="usage",
            subtype="bad_args",
            message=message,
            hint="Pass an existing local file path or a supported i讯飞 document URL.",
        )
    if args.out_dir:
        manifest = write_outputs(results, Path(args.out_dir).expanduser())
        if args.print_manifest:
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    multiple = len(results) > 1
    for result in results:
        if multiple:
            print(f"=== {result['source']} ({result['kind']}) ===")
        sys.stdout.write(str(result["content"]))
        if not str(result["content"]).endswith("\n"):
            print()
    return 0


def read_local_source(source: str) -> dict[str, object]:
    path = Path(source).expanduser()
    if not path.exists():
        fail(
            error_type="usage",
            subtype="bad_args",
            message=f"local file not found: {path}",
            hint="Pass an existing local file path or a supported i讯飞 document URL.",
        )
    return {
        "source": source,
        "kind": "local_markdown",
        "title": path.name,
        "token": "",
        "content": path.read_text(encoding="utf-8"),
        "counts": {},
    }


def write_outputs(results: list[dict[str, object]], out_dir: Path) -> dict[str, dict[str, object]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, object]] = {}
    for index, result in enumerate(results, start=1):
        stem = f"{result['kind']}_{index}"
        path = out_dir / f"{slugify(stem)}.md"
        path.write_text(str(result["content"]), encoding="utf-8")
        result["file"] = str(path)
        manifest[stem] = {
            "title": result["title"],
            "token": result["token"],
            "kind": result["kind"],
            "counts": result["counts"],
            "file": str(path),
            "source": result["source"],
        }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return text or "doc"


def run_doctor(args: argparse.Namespace) -> int:
    payload = {
        "ok": True,
        "cli": "ixfdoc",
        "version": __version__,
        "platform": platform_name(),
        "python": platform.python_version(),
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"ixfdoc {__version__}")
        print(f"platform {payload['platform']}")
        print(f"python {payload['python']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"ixfdoc {__version__}")
        return 0
    if args.command == "read":
        return run_read(args)
    if args.command == "doctor":
        return run_doctor(args)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
