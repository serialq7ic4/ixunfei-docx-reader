from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
