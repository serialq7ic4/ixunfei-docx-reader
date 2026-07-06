from pathlib import Path

import pytest

from ixunfei_docx_reader.cookies.windows_larkshell import export_cookies, find_cookie_db


def test_find_cookie_db_returns_explicit_path(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    db.write_bytes(b"sqlite")

    assert find_cookie_db(cookies_db=db, app_data=None) == db


def test_find_cookie_db_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Windows LarkShell cookie DB not found"):
        find_cookie_db(cookies_db=None, app_data=tmp_path)


def test_export_cookies_reports_decryption_not_implemented(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    db.write_bytes(b"sqlite")

    with pytest.raises(RuntimeError, match="Windows cookie decryption is not implemented yet"):
        export_cookies(output=tmp_path / "cookies.json", cookies_db=db)


def test_export_cookies_accepts_output_as_positional_argument(tmp_path: Path) -> None:
    db = tmp_path / "Cookies"
    db.write_bytes(b"sqlite")

    with pytest.raises(RuntimeError, match="Windows cookie decryption is not implemented yet"):
        export_cookies(tmp_path / "cookies.json", cookies_db=db)
