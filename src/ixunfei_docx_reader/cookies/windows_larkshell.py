from __future__ import annotations

from pathlib import Path


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


def export_cookies(
    output: Path,
    app_data: Path | None = None,
    cookies_db: Path | None = None,
    host_like: str = DEFAULT_HOST_LIKE,
) -> dict[str, object]:
    find_cookie_db(cookies_db=cookies_db, app_data=app_data)
    raise RuntimeError("Windows cookie decryption is not implemented yet.")
