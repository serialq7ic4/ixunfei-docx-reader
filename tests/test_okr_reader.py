from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import ixunfei_docx_reader.reader as reader


@dataclass
class FakeResponse:
    payload: dict[str, Any]
    text: str = ""

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeCookies:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, name: str, default: str = "") -> str:
        return self.values.get(name, default)


class FakeSession:
    def __init__(self) -> None:
        self.cookies = FakeCookies()
        self.get_calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.get_calls.append((url, kwargs))
        if url == "https://www.xfchat.iflytek.com/lgw/csrf_token":
            self.cookies.values["lgw_csrf_token"] = "lgw-fixture"
            return FakeResponse({})
        if "/okrx/api/okr/owner/aggr_detail/" in url:
            return FakeResponse(
                {
                    "code": 0,
                    "message": "",
                    "okr_detail_data": {
                        "name": "2026 年 7 月 - 9 月",
                        "owner_info": {
                            "user_info": {
                                "locale_names": {"zh": "Fixture Owner"},
                            }
                        },
                        "objective_list": [
                            {
                                "id": "o1",
                                "name": {
                                    "blocks": [
                                        {
                                            "text": "支撑计算平台规模化落地",
                                        }
                                    ]
                                },
                                "kr_list": [
                                    {
                                        "id": "kr1",
                                        "content": {
                                            "blocks": [
                                                {
                                                    "text": "SAE 生产应用数提升到 8000",
                                                }
                                            ]
                                        },
                                        "progress_rate": {"percent": 20},
                                    },
                                    {
                                        "id": "kr2",
                                        "content_v2": {
                                            "0": {
                                                "ops": [
                                                    {
                                                        "insert": "KubeVirt 云主机提升到 500+\n",
                                                    }
                                                ]
                                            }
                                        },
                                    },
                                ],
                            }
                        ],
                    },
                }
            )
        raise AssertionError(f"unexpected GET {url}")


def test_detect_remote_kind_recognizes_okr_url() -> None:
    assert (
        reader.detect_remote_kind(
            "https://example.xfchat.iflytek.com/okr/user/1000000000000000000/"
            "?okrId=2000000000000000000"
        )
        == "okr"
    )


def test_read_okr_uses_lgw_csrf_and_okr_id_query_param() -> None:
    session = FakeSession()

    title, token, body, counts = reader.read_okr(
        session,  # type: ignore[arg-type]
        "https://example.xfchat.iflytek.com/okr/user/1000000000000000000/"
        "?lang=zh-CN&okrId=2000000000000000000&type=leader",
    )

    assert title == "OKR - Fixture Owner - 2026 年 7 月 - 9 月"
    assert token == "2000000000000000000"
    assert counts == {"objectives": 1, "key_results": 2}
    assert "# OKR - Fixture Owner - 2026 年 7 月 - 9 月" in body
    assert "## O1 支撑计算平台规模化落地" in body
    assert "- KR1: SAE 生产应用数提升到 8000 _(progress: 20%)_" in body
    assert "- KR2: KubeVirt 云主机提升到 500+" in body

    urls = [call[0] for call in session.get_calls]
    assert urls[0] == "https://www.xfchat.iflytek.com/lgw/csrf_token"
    detail_url, detail_kwargs = session.get_calls[1]
    assert "/okrx/api/okr/owner/aggr_detail/" in detail_url
    assert "okr_id=2000000000000000000" in detail_url
    assert "okrId=" not in detail_url
    assert detail_kwargs["headers"]["x-lgw-csrf-token"] == "lgw-fixture"
