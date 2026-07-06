from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sqlite3
import sys
from pathlib import Path
from typing import NoReturn

import requests

from ixunfei_docx_reader import __version__
from ixunfei_docx_reader.cookies.macos_larkshell import (
    DEFAULT_APP_SUPPORT,
    DEFAULT_HOST_LIKE,
    DEFAULT_KEYCHAIN_ACCOUNT,
    DEFAULT_KEYCHAIN_SERVICE,
    export_cookies as export_macos_larkshell_cookies,
)
from ixunfei_docx_reader.cookies.windows_larkshell import (
    export_cookies as export_windows_larkshell_cookies,
)
from ixunfei_docx_reader.reader import DEFAULT_COOKIES, DEFAULT_SPACE_API, read_sources
from ixunfei_docx_reader.reader import load_cookie_objects


EXIT_CODES = {
    "bad_args": 2,
    "cookie_file_missing": 5,
    "cookie_export_failed": 6,
    "cookie_file_invalid": 7,
    "cookie_csrf_missing": 8,
    "remote_read_failed": 9,
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
    doctor.add_argument("--cookies", default=DEFAULT_COOKIES)

    cookies = subparsers.add_parser("cookies", help="Manage local session cookies.")
    cookie_subparsers = cookies.add_subparsers(dest="cookies_command")
    cookie_subparsers.required = True
    export = cookie_subparsers.add_parser("export", help="Export local LarkShell cookies.")
    export.add_argument(
        "--provider",
        default="auto",
        choices=["auto", "macos-larkshell", "windows-larkshell"],
    )
    export.add_argument("--output", default=DEFAULT_COOKIES)
    export.add_argument("--app-support", default=DEFAULT_APP_SUPPORT)
    export.add_argument("--cookies-db", default="")
    export.add_argument("--host-like", default=DEFAULT_HOST_LIKE)
    export.add_argument("--keychain-service", default=DEFAULT_KEYCHAIN_SERVICE)
    export.add_argument("--keychain-account", default=DEFAULT_KEYCHAIN_ACCOUNT)

    setup = subparsers.add_parser("setup", help="Install local agent integration helpers.")
    setup_subparsers = setup.add_subparsers(dest="setup_command")
    setup_subparsers.required = True
    setup_skills = setup_subparsers.add_parser(
        "skills",
        help="Install Codex/Claude Code skill wrappers.",
    )
    setup_skills.add_argument("--runtimes", default="auto")
    setup_skills.add_argument("--force", action="store_true")
    setup_skills.add_argument("--json", action="store_true", dest="as_json")

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
    except ValueError as exc:
        message = str(exc)
        if message == "Cookie jar does not contain _csrf_token.":
            fail(
                error_type="cookie",
                subtype="cookie_csrf_missing",
                message=message,
                hint="Run `ixfdoc cookies export --provider auto --output <path>` to refresh the local desktop session cookies.",
            )
        fail(
            error_type="cookie",
            subtype="cookie_file_invalid",
            message=message,
            hint="Run `ixfdoc cookies export --provider auto --output <path>` or pass a valid --cookies file.",
        )
    except (requests.RequestException, RuntimeError) as exc:
        fail(
            error_type="remote",
            subtype="remote_read_failed",
            message=str(exc),
            hint="Check network access, document permissions, and whether the local desktop session is still valid.",
            retryable=True,
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
        "cookies": cookie_diagnostics(Path(args.cookies).expanduser()),
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"ixfdoc {__version__}")
        print(f"platform {payload['platform']}")
        print(f"python {payload['python']}")
        cookie_info = payload["cookies"]
        print(f"cookies {cookie_info['path']}")
        print(f"cookies.exists {cookie_info['exists']}")
        print(f"cookies.hasCsrf {cookie_info['hasCsrf']}")
    return 0


def cookie_diagnostics(cookie_path: Path) -> dict[str, object]:
    payload: dict[str, object] = {
        "path": str(cookie_path),
        "exists": cookie_path.exists(),
        "readable": False,
        "cookieCount": 0,
        "hasCsrf": False,
    }
    if not cookie_path.exists():
        return payload
    try:
        cookies = load_cookie_objects(cookie_path)
    except Exception as exc:
        payload["error"] = str(exc)
        return payload
    payload["readable"] = True
    payload["cookieCount"] = len(cookies)
    payload["hasCsrf"] = any(
        cookie.get("name") == "_csrf_token" and bool(cookie.get("value")) for cookie in cookies
    )
    return payload


def run_cookies(args: argparse.Namespace) -> int:
    if args.cookies_command == "export":
        provider = args.provider
        if provider == "auto":
            provider = "windows-larkshell" if platform_name() == "windows" else "macos-larkshell"
        if provider == "windows-larkshell":
            try:
                payload = export_windows_larkshell_cookies(
                    output=Path(args.output).expanduser(),
                    cookies_db=Path(args.cookies_db).expanduser() if args.cookies_db else None,
                    host_like=args.host_like,
                )
            except (FileNotFoundError, RuntimeError, sqlite3.Error, OSError) as exc:
                fail(
                    error_type="cookie",
                    subtype="cookie_export_failed",
                    message=str(exc),
                    hint="Open i讯飞/LarkShell desktop on Windows, confirm you are logged in, then retry.",
                    retryable=True,
                )
            print(json.dumps(payload, ensure_ascii=False))
            return 0
        try:
            payload = export_macos_larkshell_cookies(
                output=Path(args.output).expanduser(),
                app_support=Path(args.app_support).expanduser(),
                cookies_db=Path(args.cookies_db).expanduser() if args.cookies_db else None,
                host_like=args.host_like,
                keychain_service=args.keychain_service,
                keychain_account=args.keychain_account,
            )
        except (FileNotFoundError, RuntimeError, sqlite3.Error) as exc:
            fail(
                error_type="cookie",
                subtype="cookie_export_failed",
                message=str(exc),
                hint="Confirm i讯飞 is installed and logged in, then retry `ixfdoc cookies export`.",
                retryable=True,
            )
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    fail(
        error_type="usage",
        subtype="bad_args",
        message="unknown cookies command.",
        hint="Run `ixfdoc cookies export --help`.",
    )


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
    if args.command == "cookies":
        return run_cookies(args)
    if args.command == "setup" and args.setup_command == "skills":
        return run_setup_skills(args)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
