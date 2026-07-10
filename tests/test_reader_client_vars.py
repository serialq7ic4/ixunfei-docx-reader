from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ixunfei_docx_reader.reader as reader
from ixunfei_docx_reader.converters.docx_markdown import ImageResolution
from ixunfei_docx_reader.reader import client_vars


@dataclass
class FakeResponse:
    payload: dict[str, Any]

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeSession:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.urls.append(url)
        if "mode=4" in url:
            return FakeResponse(
                {
                    "code": 0,
                    "data": {
                        "block_map": {
                            "text_2": {
                                "data": {
                                    "type": "text",
                                    "parent_id": "page_1",
                                    "text": {"initialAttributedTexts": {"text": {"0": "later"}}},
                                }
                            }
                        },
                        "has_more": False,
                    },
                }
            )
        return FakeResponse(
            {
                "code": 0,
                "data": {
                    "block_map": {
                        "page_1": {
                            "data": {
                                "type": "page",
                                "children": ["text_1", "text_2"],
                            }
                        },
                        "text_1": {
                            "data": {
                                "type": "text",
                                "parent_id": "page_1",
                                "text": {"initialAttributedTexts": {"text": {"0": "first"}}},
                            }
                        },
                    },
                    "has_more": True,
                    "cursor": "next-cursor",
                },
            }
        )


def test_client_vars_merges_cursor_pages_into_initial_payload() -> None:
    session = FakeSession()

    data = client_vars(
        session,  # type: ignore[arg-type]
        "https://internal-api-space.xfchat.iflytek.com",
        "page_1",
        "https://example.com",
        "csrf-fixture",
    )

    assert list(data["block_map"]) == ["page_1", "text_1", "text_2"]
    assert len(session.urls) == 2
    assert "mode=4" in session.urls[1]
    assert "cursor=next-cursor" in session.urls[1]


def test_read_remote_uses_readable_text_for_rich_text_page_title(monkeypatch: Any) -> None:
    client_vars_data = {
        "block_map": {
            "page_1": {
                "data": {
                    "type": "page",
                    "children": [],
                    "text": {
                        "apool": {"nextNum": 1},
                        "initialAttributedTexts": {
                            "attribs": {"0": "*0+e"},
                            "text": {"0": "Readable Title"},
                        },
                    },
                }
            }
        }
    }
    monkeypatch.setattr(reader, "fetch_html", lambda *args: "")
    monkeypatch.setattr(reader, "extract_doc_token", lambda *args: "page_1")
    monkeypatch.setattr(reader, "client_vars", lambda *args: client_vars_data)

    _, title, _, body, _, assets, warnings = reader.read_remote(
        object(),  # type: ignore[arg-type]
        "https://example.com/docx/page_1",
        "https://internal-api-space.xfchat.iflytek.com",
        "csrf-fixture",
        False,
    )

    assert title == "Readable Title"
    assert body == "# Readable Title\n"
    assert assets == []
    assert warnings == []


def test_read_remote_uses_image_asset_writer_when_enabled(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    client_vars_data = {
        "block_map": {
            "page_1": {
                "data": {
                    "type": "page",
                    "children": ["image_1"],
                    "text": {"initialAttributedTexts": {"text": {"0": "Image Doc"}}},
                }
            },
            "image_1": {
                "data": {
                    "type": "image",
                    "parent_id": "page_1",
                    "image": {
                        "token": "boxr-private-token",
                        "name": "architecture.png",
                        "mimeType": "image/png",
                        "width": 1200,
                        "height": 800,
                        "size": 1234,
                        "caption": {
                            "initialAttributedTexts": {
                                "text": {"0": "Architecture diagram"}
                            }
                        },
                    },
                }
            },
        }
    }
    created: list[dict[str, Any]] = []

    class StubImageAssetWriter:
        def __init__(self, **kwargs: Any) -> None:
            created.append(kwargs)

        def resolve(self, _reference: object) -> ImageResolution:
            return ImageResolution(
                markdown_path="assets/docx_1/image-001.png",
                alt_text="Architecture diagram",
                asset={
                    "path": "assets/docx_1/image-001.png",
                    "mimeType": "image/png",
                    "width": 1200,
                    "height": 800,
                    "sizeBytes": 1234,
                    "status": "downloaded",
                    "ordinal": 1,
                },
            )

    monkeypatch.setattr(reader, "fetch_html", lambda *args: "")
    monkeypatch.setattr(reader, "extract_doc_token", lambda *args: "page_1")
    monkeypatch.setattr(reader, "client_vars", lambda *args: client_vars_data)
    monkeypatch.setattr(reader, "ImageAssetWriter", StubImageAssetWriter)
    session = object()

    kind, title, token, body, counts, assets, warnings = reader.read_remote(
        session,  # type: ignore[arg-type]
        "https://example.com/docx/page_1",
        "https://internal-api-space.xfchat.iflytek.com",
        "csrf-fixture",
        False,
        download_images=True,
        output_root=tmp_path,
        asset_group="docx_1",
    )

    assert kind == "docx"
    assert title == "Image Doc"
    assert token == "page_1"
    assert body == (
        "# Image Doc\n\n"
        "![Architecture diagram](assets/docx_1/image-001.png)\n"
    )
    assert counts["image"] == 1
    assert assets == [
        {
            "path": "assets/docx_1/image-001.png",
            "mimeType": "image/png",
            "width": 1200,
            "height": 800,
            "sizeBytes": 1234,
            "status": "downloaded",
            "ordinal": 1,
        }
    ]
    assert warnings == []
    assert len(created) == 1
    assert created[0]["session"] is session
    assert created[0] == {
        "session": session,
        "origin": "https://example.com",
        "referer": "https://example.com/docx/page_1",
        "headers": {
            "User-Agent": reader.USER_AGENT,
            "Origin": "https://example.com",
            "Referer": "https://example.com/docx/page_1",
            "X-CSRFToken": "csrf-fixture",
        },
        "document_token": "page_1",
        "output_root": tmp_path,
        "asset_group": "docx_1",
    }


def test_read_sources_requires_output_root_when_downloading_images() -> None:
    try:
        reader.read_sources(["local.md"], download_images=True)
    except ValueError as exc:
        assert str(exc) == "download_images requires output_root."
    else:
        raise AssertionError("expected download_images output_root validation")
