from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
import sqlite3
from typing import Any


DEFAULT_HOST_LIKE = "%xfchat.iflytek.com%"


def find_cookie_db(cookies_db: Path | None, app_data: Path | None) -> Path:
    if cookies_db is not None:
        path = cookies_db.expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"Windows LarkShell cookie DB not found: {path}")
    if app_data is None:
        raise FileNotFoundError("Windows LarkShell cookie DB not found: APPDATA is not set")
    candidates = [
        app_data / "LarkShell" / "User Data" / "Default" / "Network" / "Cookies",
        app_data / "LarkShell" / "User Data" / "Default" / "Cookies",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Windows LarkShell cookie DB not found under APPDATA")


def row_to_cookie(row: dict[str, Any], decrypt_value: Callable[[bytes], str]) -> dict[str, object]:
    value = str(row.get("value") or "")
    encrypted = row.get("encrypted_value") or b""
    if not value and encrypted:
        value = decrypt_value(bytes(encrypted))
    return {
        "domain": str(row["host_key"]),
        "name": str(row["name"]),
        "value": value,
        "path": str(row.get("path") or "/"),
        "secure": bool(row.get("is_secure")),
    }


def export_cookies_from_db(
    db_path: Path,
    output: Path,
    host_like: str,
    decrypt_value: Callable[[bytes], str],
) -> dict[str, object]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT host_key, name, value, encrypted_value, path, is_secure
            FROM cookies
            WHERE host_key LIKE ?
            ORDER BY host_key, name
            """,
            (host_like,),
        ).fetchall()
    finally:
        conn.close()
    cookies = [row_to_cookie(dict(row), decrypt_value) for row in rows]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(output, 0o600)
    except OSError:
        pass
    return {
        "ok": True,
        "provider": "windows-larkshell",
        "output": str(output),
        "cookieCount": len(cookies),
        "hasCsrf": any(cookie["name"] == "_csrf_token" for cookie in cookies),
    }


def decrypt_dpapi_value(encrypted_value: bytes) -> str:
    try:
        import win32crypt
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is required on Windows. Install with `python -m pip install -e \".[windows]\"`."
        ) from exc
    _, decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)
    return decrypted.decode("utf-8")


def export_cookies(
    output: Path,
    app_data: Path | None = None,
    cookies_db: Path | None = None,
    host_like: str = DEFAULT_HOST_LIKE,
) -> dict[str, object]:
    if app_data is None:
        raw_app_data = os.environ.get("APPDATA")
        app_data = Path(raw_app_data) if raw_app_data else None
    db_path = find_cookie_db(cookies_db=cookies_db, app_data=app_data)
    return export_cookies_from_db(db_path, output, host_like, decrypt_dpapi_value)
