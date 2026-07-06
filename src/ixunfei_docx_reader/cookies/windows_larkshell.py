from __future__ import annotations

import base64
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


def find_local_state(
    local_state: Path | None,
    app_data: Path | None,
    cookies_db: Path | None,
) -> Path:
    if local_state is not None:
        path = local_state.expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"Windows LarkShell Local State not found: {path}")
    if cookies_db is not None:
        path = cookies_db.expanduser()
        candidates = [
            path.parent.parent.parent / "Local State",
            path.parent.parent / "Local State",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
    if app_data is None:
        raise FileNotFoundError("Windows LarkShell Local State not found: APPDATA is not set")
    candidate = app_data / "LarkShell" / "User Data" / "Local State"
    if candidate.exists():
        return candidate
    raise FileNotFoundError("Windows LarkShell Local State not found under APPDATA")


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


def has_non_empty_csrf(cookies: list[dict[str, object]]) -> bool:
    return any(
        cookie.get("name") == "_csrf_token" and bool(str(cookie.get("value") or ""))
        for cookie in cookies
    )


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
        "hasCsrf": has_non_empty_csrf(cookies),
    }


def dpapi_unprotect(encrypted_value: bytes) -> bytes:
    try:
        import win32crypt
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is required on Windows. Install with `python -m pip install -e \".[windows]\"`."
        ) from exc
    _, decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)
    return bytes(decrypted)


def unwrap_local_state_key(
    encrypted_key: str,
    dpapi_unprotect: Callable[[bytes], bytes] = dpapi_unprotect,
) -> bytes:
    wrapped_key = base64.b64decode(encrypted_key)
    if wrapped_key.startswith(b"DPAPI"):
        wrapped_key = wrapped_key[len(b"DPAPI") :]
    return dpapi_unprotect(wrapped_key)


def load_local_state_master_key(
    local_state: Path,
    dpapi_unprotect: Callable[[bytes], bytes] = dpapi_unprotect,
) -> bytes:
    payload = json.loads(local_state.read_text(encoding="utf-8"))
    encrypted_key = payload.get("os_crypt", {}).get("encrypted_key")
    if not isinstance(encrypted_key, str) or not encrypted_key:
        raise RuntimeError("Windows LarkShell Local State does not contain os_crypt.encrypted_key")
    return unwrap_local_state_key(encrypted_key, dpapi_unprotect=dpapi_unprotect)


def decrypt_chromium_cookie_value(
    encrypted_value: bytes,
    master_key: bytes,
    dpapi_unprotect: Callable[[bytes], bytes] = dpapi_unprotect,
) -> str:
    if encrypted_value.startswith((b"v10", b"v11")):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError as exc:
            raise RuntimeError(
                "cryptography is required for modern Windows Chromium cookies. "
                "Install with `python -m pip install -e \".[windows]\"`."
            ) from exc
        nonce = encrypted_value[3:15]
        ciphertext_and_tag = encrypted_value[15:]
        if len(nonce) != 12 or len(ciphertext_and_tag) < 16:
            raise RuntimeError("Chromium cookie encrypted_value is not a valid AES-GCM blob")
        return AESGCM(master_key).decrypt(nonce, ciphertext_and_tag, None).decode("utf-8")
    return dpapi_unprotect(encrypted_value).decode("utf-8")


def decrypt_dpapi_value(encrypted_value: bytes) -> str:
    return dpapi_unprotect(encrypted_value).decode("utf-8")


def export_cookies(
    output: Path,
    app_data: Path | None = None,
    cookies_db: Path | None = None,
    local_state: Path | None = None,
    host_like: str = DEFAULT_HOST_LIKE,
    dpapi_unprotect: Callable[[bytes], bytes] = dpapi_unprotect,
) -> dict[str, object]:
    if app_data is None:
        raw_app_data = os.environ.get("APPDATA")
        app_data = Path(raw_app_data) if raw_app_data else None
    db_path = find_cookie_db(cookies_db=cookies_db, app_data=app_data)
    master_key: bytes | None = None

    def decrypt_value(encrypted_value: bytes) -> str:
        nonlocal master_key
        if encrypted_value.startswith((b"v10", b"v11")):
            if master_key is None:
                state_path = find_local_state(
                    local_state=local_state,
                    app_data=app_data,
                    cookies_db=db_path,
                )
                master_key = load_local_state_master_key(
                    state_path,
                    dpapi_unprotect=dpapi_unprotect,
                )
            return decrypt_chromium_cookie_value(
                encrypted_value,
                master_key=master_key,
                dpapi_unprotect=dpapi_unprotect,
            )
        return dpapi_unprotect(encrypted_value).decode("utf-8")

    return export_cookies_from_db(
        db_path,
        output,
        host_like,
        decrypt_value,
    )
