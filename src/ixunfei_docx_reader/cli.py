from __future__ import annotations

import argparse
import contextlib
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
    "update_check_failed": 10,
}

DEFAULT_RELEASE_REPO = "serialq7ic4/ixunfei-docx-reader"


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
    read.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove generated Markdown and manifest files before exiting.",
    )
    read.add_argument("--cookies", default=DEFAULT_COOKIES)
    read.add_argument("--space-api", default=DEFAULT_SPACE_API)

    inspect = subparsers.add_parser("inspect", help="Print a safe source routing summary.")
    inspect.add_argument("source")
    inspect.add_argument("--json", action="store_true", dest="as_json")

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

    update = subparsers.add_parser("update", help="Check releases and refresh local skills.")
    update_subparsers = update.add_subparsers(dest="update_command")
    update_subparsers.required = True
    update_check = update_subparsers.add_parser("check", help="Check the latest GitHub Release.")
    update_check.add_argument("--repo", default=DEFAULT_RELEASE_REPO)
    update_check.add_argument("--json", action="store_true", dest="as_json")
    update_skills = update_subparsers.add_parser(
        "skills",
        help="Refresh installed Codex/Claude Code skill wrappers from this package.",
    )
    update_skills.add_argument("--runtimes", default="auto")
    update_skills.add_argument("--json", action="store_true", dest="as_json")

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
        out_dir = Path(args.out_dir).expanduser()
        manifest = write_outputs(results, out_dir)
        if args.print_manifest:
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
        if args.cleanup:
            cleanup_outputs(manifest, out_dir)
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
    used_stems: set[str] = set()
    for index, result in enumerate(results, start=1):
        stem = f"{result['kind']}_{index}"
        path = out_dir / f"{output_file_stem(result, stem, used_stems)}.md"
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


def cleanup_outputs(manifest: dict[str, dict[str, object]], out_dir: Path) -> None:
    generated_paths = [Path(str(item["file"])) for item in manifest.values()]
    generated_paths.append(out_dir / "manifest.json")
    for path in generated_paths:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
    with contextlib.suppress(OSError):
        out_dir.rmdir()


def slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return text or "doc"


def output_file_stem(result: dict[str, object], fallback: str, used_stems: set[str]) -> str:
    base = slugify(fallback)
    if result.get("kind") == "local_markdown":
        source = Path(str(result.get("source", ""))).expanduser()
        base = slugify(source.stem or str(result.get("title", "")) or fallback)

    candidate = base
    suffix = 2
    while candidate in used_stems:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used_stems.add(candidate)
    return candidate


def run_inspect(args: argparse.Namespace) -> int:
    payload = inspect_source(args.source)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        source_key = "sourceRef" if payload["remote"] else "source"
        print(f"source {payload[source_key]}")
        print(f"remote {str(payload['remote']).lower()}")
        print(f"kind {payload['kind']}")
        if payload["remote"]:
            print(f"host {payload['host']}")
            print(f"route {payload['route']}")
        else:
            print(f"path {payload['path']}")
            print(f"exists {str(payload['exists']).lower()}")
            print(f"readable {str(payload['readable']).lower()}")
    return 0


def inspect_source(source: str) -> dict[str, object]:
    if source.startswith(("http://", "https://")):
        return inspect_remote_source(source)
    return inspect_local_source(source)


def inspect_local_source(source: str) -> dict[str, object]:
    path = Path(source).expanduser()
    if not path.exists():
        fail(
            error_type="usage",
            subtype="bad_args",
            message=f"local file not found: {path}",
            hint="Pass an existing local path or a supported i讯飞 document URL.",
        )
    return {
        "ok": True,
        "source": source,
        "remote": False,
        "kind": "local_markdown",
        "path": str(path),
        "exists": True,
        "readable": os.access(path, os.R_OK),
        "sizeBytes": path.stat().st_size,
        "suffix": path.suffix,
    }


def inspect_remote_source(source: str) -> dict[str, object]:
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(source)
    path = parsed.path
    path_type = "remote"
    token = ""
    owner_id = ""
    kind = "remote"
    route = "remote_read"

    if "/okr/user/" in path:
        path_type = "okr"
        owner_match = re.search(r"/okr/user/([^/?#]+)", path)
        if owner_match:
            owner_id = owner_match.group(1)
        query = parse_qs(parsed.query)
        token = (query.get("okrId") or query.get("okr_id") or [""])[0]
    else:
        for candidate in ("docx", "wiki", "mindnotes"):
            match = re.search(rf"/{candidate}/([^/?#]+)", path)
            if match:
                path_type = candidate
                token = match.group(1)
                break

    if path_type == "docx":
        kind = "docx"
        route = "docx_client_vars"
    elif path_type == "wiki":
        kind = "wiki"
        route = "wiki_resolve_then_read"
    elif path_type == "mindnotes":
        kind = "mindnote"
        route = "mindnote_client_vars"
    elif path_type == "okr":
        kind = "okr"
        route = "okr_detail"

    return {
        "ok": True,
        "sourceRef": redacted_remote_source(
            parsed.path,
            parsed.netloc,
            parsed.query,
            [owner_id, token],
        ),
        "remote": True,
        "kind": kind,
        "host": parsed.netloc,
        "pathType": path_type,
        "tokenPrefix": token[:3],
        "tokenLength": len(token),
        "route": route,
    }


def redacted_remote_source(
    path: str,
    netloc: str,
    query: str,
    tokens: list[str],
) -> str:
    redacted_path = path
    redacted_query = query
    for token in tokens:
        if not token:
            continue
        redacted_path = redacted_path.replace(token, "<redacted>")
        redacted_query = redacted_query.replace(token, "<redacted>")
    suffix = f"?{redacted_query}" if redacted_query else ""
    return f"https://{netloc}{redacted_path}{suffix}"


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
    try:
        payload = install_packaged_skill_wrappers(
            packaged_resource_root(),
            Path.home(),
            args.runtimes.split(","),
            args.force,
            dict(os.environ),
        )
    except ValueError as exc:
        fail(
            error_type="usage",
            subtype="bad_args",
            message=str(exc),
            hint="Use --runtimes auto, all, none, codex, claude-code, or a comma-separated supported list.",
        )
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"installed {len(payload['installed'])} wrapper(s)")
        if payload["skipped"]:
            print(
                f"skipped {len(payload['skipped'])} existing wrapper(s); "
                "pass --force to overwrite"
            )
    return 0


def packaged_resource_root() -> Path:
    from ixunfei_docx_reader.setup import packaged_project_root

    return packaged_project_root()


def install_packaged_skill_wrappers(
    project_root: Path,
    home: Path,
    runtimes: list[str],
    force: bool,
    env: dict[str, str],
) -> dict[str, object]:
    from ixunfei_docx_reader.setup import install_skill_wrappers

    return install_skill_wrappers(project_root, home, runtimes, force, env)


def get_latest_github_release(repo: str) -> dict[str, object]:
    response = requests.get(
        f"https://api.github.com/repos/{repo}/releases/latest",
        headers={"Accept": "application/vnd.github+json"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub release response was not a JSON object.")
    return payload


def normalize_release_version(tag: str) -> str:
    return tag.strip().removeprefix("v").removeprefix("V")


def parse_version_parts(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for raw_part in normalize_release_version(version).split("."):
        match = re.match(r"^(\d+)", raw_part)
        if match is None:
            break
        parts.append(int(match.group(1)))
    return tuple(parts)


def is_newer_version(candidate: str, current: str) -> bool:
    candidate_parts = parse_version_parts(candidate)
    current_parts = parse_version_parts(current)
    width = max(len(candidate_parts), len(current_parts))
    candidate_parts = candidate_parts + (0,) * (width - len(candidate_parts))
    current_parts = current_parts + (0,) * (width - len(current_parts))
    return candidate_parts > current_parts


def release_install_command(repo: str, version: str) -> str:
    extra = "windows" if platform_name() == "windows" else "crypto"
    return (
        "python -m pip install --upgrade "
        f"\"ixunfei-docx-reader[{extra}] @ https://github.com/{repo}/releases/download/"
        f"v{version}/ixunfei_docx_reader-{version}-py3-none-any.whl\" && "
        "ixfdoc update skills --runtimes auto --json"
    )


def build_update_check_payload(repo: str, release: dict[str, object]) -> dict[str, object]:
    latest_tag = str(release.get("tag_name", "")).strip()
    if not latest_tag:
        raise RuntimeError("GitHub release response did not include tag_name.")
    latest_version = normalize_release_version(latest_tag)
    release_url = str(release.get("html_url", ""))
    update_available = is_newer_version(latest_version, __version__)
    return {
        "ok": True,
        "currentVersion": __version__,
        "latestVersion": latest_version,
        "latestTag": latest_tag,
        "updateAvailable": update_available,
        "releaseUrl": release_url,
        "installCommand": release_install_command(repo, latest_version) if update_available else "",
    }


def run_update_check(args: argparse.Namespace) -> int:
    try:
        payload = build_update_check_payload(args.repo, get_latest_github_release(args.repo))
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        fail(
            error_type="remote",
            subtype="update_check_failed",
            message=str(exc),
            hint="Check network access and the GitHub repo name, then retry `ixfdoc update check`.",
            retryable=True,
        )
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"current {payload['currentVersion']}")
        print(f"latest {payload['latestVersion']}")
        print(f"updateAvailable {str(payload['updateAvailable']).lower()}")
        if payload["releaseUrl"]:
            print(f"release {payload['releaseUrl']}")
        if payload["updateAvailable"]:
            print("install:")
            print(payload["installCommand"])
    return 0


def run_update_skills(args: argparse.Namespace) -> int:
    try:
        payload = install_packaged_skill_wrappers(
            packaged_resource_root(),
            Path.home(),
            args.runtimes.split(","),
            True,
            dict(os.environ),
        )
    except ValueError as exc:
        fail(
            error_type="usage",
            subtype="bad_args",
            message=str(exc),
            hint="Use --runtimes auto, all, none, codex, claude-code, or a comma-separated supported list.",
        )
    payload = {**payload, "updated": True}
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"updated {len(payload['installed'])} wrapper(s)")
        if payload["skipped"]:
            print(f"skipped {len(payload['skipped'])} wrapper(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"ixfdoc {__version__}")
        return 0
    if args.command == "read":
        return run_read(args)
    if args.command == "inspect":
        return run_inspect(args)
    if args.command == "doctor":
        return run_doctor(args)
    if args.command == "cookies":
        return run_cookies(args)
    if args.command == "setup" and args.setup_command == "skills":
        return run_setup_skills(args)
    if args.command == "update" and args.update_command == "check":
        return run_update_check(args)
    if args.command == "update" and args.update_command == "skills":
        return run_update_skills(args)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
