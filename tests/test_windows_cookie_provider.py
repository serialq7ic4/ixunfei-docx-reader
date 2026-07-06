from pathlib import Path
import json
import sqlite3
from unittest.mock import patch

import pytest

from ixunfei_docx_reader.cookies.windows_larkshell import (
    export_cookies,
    export_cookies_from_db,
    find_cookie_db,
    row_to_cookie,
)


def test_find_cookie_db_returns_explicit_path(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    db.write_bytes(b"sqlite")

    assert find_cookie_db(cookies_db=db, app_data=None) == db


def test_find_cookie_db_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Windows LarkShell cookie DB not found"):
        find_cookie_db(cookies_db=None, app_data=tmp_path)


def test_row_to_cookie_uses_plain_value_when_present() -> None:
    row = {
        "host_key": ".xfchat.iflytek.com",
        "name": "_csrf_token",
        "value": "plain",
        "encrypted_value": b"",
        "path": "/",
        "is_secure": 1,
    }

    cookie = row_to_cookie(row, decrypt_value=lambda value: "decrypted")

    assert cookie["value"] == "plain"
    assert cookie["secure"] is True


def test_row_to_cookie_decrypts_encrypted_value() -> None:
    row = {
        "host_key": ".xfchat.iflytek.com",
        "name": "session",
        "value": "",
        "encrypted_value": b"encrypted",
        "path": "/",
        "is_secure": 0,
    }

    cookie = row_to_cookie(row, decrypt_value=lambda value: "secret")

    assert cookie["value"] == "secret"
    assert cookie["secure"] is False


def test_export_cookies_from_db_writes_browser_cookie_json(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE cookies (
            host_key TEXT,
            name TEXT,
            value TEXT,
            encrypted_value BLOB,
            path TEXT,
            is_secure INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO cookies VALUES (?, ?, ?, ?, ?, ?)",
        (".xfchat.iflytek.com", "_csrf_token", "", b"encrypted", "/", 1),
    )
    conn.commit()
    conn.close()
    output = tmp_path / "cookies.json"

    payload = export_cookies_from_db(
        db,
        output,
        "%xfchat.iflytek.com%",
        decrypt_value=lambda value: "csrf",
    )

    assert payload["cookieCount"] == 1
    assert payload["hasCsrf"] is True
    cookies = json.loads(output.read_text(encoding="utf-8"))
    assert [cookie["value"] for cookie in cookies] == ["csrf"]


def test_export_cookies_uses_injected_dpapi_decryptor(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE cookies (
            host_key TEXT,
            name TEXT,
            value TEXT,
            encrypted_value BLOB,
            path TEXT,
            is_secure INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO cookies VALUES (?, ?, ?, ?, ?, ?)",
        (".xfchat.iflytek.com", "_csrf_token", "", b"encrypted", "/", 1),
    )
    conn.commit()
    conn.close()
    output = tmp_path / "cookies.json"

    with patch(
        "ixunfei_docx_reader.cookies.windows_larkshell.decrypt_dpapi_value",
        return_value="csrf",
    ):
        payload = export_cookies(output=output, cookies_db=db)

    assert payload["ok"] is True
    assert payload["cookieCount"] == 1


def test_export_cookies_accepts_output_as_positional_argument(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE cookies (
            host_key TEXT,
            name TEXT,
            value TEXT,
            encrypted_value BLOB,
            path TEXT,
            is_secure INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO cookies VALUES (?, ?, ?, ?, ?, ?)",
        (".xfchat.iflytek.com", "_csrf_token", "plain", b"", "/", 1),
    )
    conn.commit()
    conn.close()

    payload = export_cookies(tmp_path / "cookies.json", cookies_db=db)

    assert payload["ok"] is True
    assert payload["cookieCount"] == 1


def test_export_cookies_uses_appdata_from_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "LarkShell" / "User Data" / "Default" / "Network" / "Cookies"
    db.parent.mkdir(parents=True)
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE cookies (
            host_key TEXT,
            name TEXT,
            value TEXT,
            encrypted_value BLOB,
            path TEXT,
            is_secure INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO cookies VALUES (?, ?, ?, ?, ?, ?)",
        (".xfchat.iflytek.com", "_csrf_token", "plain", b"", "/", 1),
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("APPDATA", str(tmp_path))

    payload = export_cookies(tmp_path / "cookies.json")

    assert payload["ok"] is True
    assert payload["cookieCount"] == 1
