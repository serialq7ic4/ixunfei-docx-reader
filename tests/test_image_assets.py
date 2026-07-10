from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from ixunfei_docx_reader.assets import ImageAssetWriter
from ixunfei_docx_reader.converters.docx_markdown import ImageReference


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


class FakeResponse:
    def __init__(
        self,
        content: bytes,
        *,
        content_type: str = "image/png",
        status_code: int = 200,
        error_detail: str = "",
    ) -> None:
        self.content = content
        self.headers = {"Content-Type": content_type}
        self.status_code = status_code
        self.error_detail = error_detail

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(
                f"status={self.status_code} private={self.error_detail}",
                response=self,  # type: ignore[arg-type]
            )

    def iter_content(self, chunk_size: int) -> list[bytes]:
        return [
            self.content[index : index + chunk_size]
            for index in range(0, len(self.content), chunk_size)
        ]

    def close(self) -> None:
        return None


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append({"url": url, **kwargs})
        return self.responses.pop(0)


def image_reference(token: str = "boxr-private-token") -> ImageReference:
    return ImageReference(
        block_id="image-block",
        token=token,
        name="architecture.png",
        mime_type="image/png",
        width=1200,
        height=800,
        declared_size=len(PNG_BYTES),
        caption="Architecture diagram",
    )


def image_writer(
    tmp_path: Path,
    session: FakeSession,
) -> ImageAssetWriter:
    return ImageAssetWriter(
        session=session,  # type: ignore[arg-type]
        origin="https://tenant.xfchat.iflytek.com",
        referer="https://tenant.xfchat.iflytek.com/docx/dox-private-document",
        headers={
            "Origin": "https://tenant.xfchat.iflytek.com",
            "Referer": "https://tenant.xfchat.iflytek.com/docx/dox-private-document",
            "X-CSRFToken": "private-csrf",
        },
        document_token="dox-private-document",
        output_root=tmp_path,
        asset_group="docx_1",
    )


def test_image_asset_writer_downloads_png_to_safe_relative_path(tmp_path: Path) -> None:
    token = "boxr-private-token"
    session = FakeSession([FakeResponse(PNG_BYTES)])
    writer = image_writer(tmp_path, session)

    resolution = writer.resolve(image_reference(token))

    assert resolution.markdown_path == "assets/docx_1/image-001.png"
    assert resolution.alt_text == "Architecture diagram"
    assert resolution.warning is None
    assert resolution.asset == {
        "path": "assets/docx_1/image-001.png",
        "mimeType": "image/png",
        "width": 1200,
        "height": 800,
        "sizeBytes": len(PNG_BYTES),
        "status": "downloaded",
        "ordinal": 1,
    }
    asset_path = tmp_path / "assets" / "docx_1" / "image-001.png"
    assert asset_path.read_bytes() == PNG_BYTES
    assert not asset_path.with_suffix(".png.part").exists()

    request = session.requests[0]
    assert request["url"] == (
        "https://tenant.xfchat.iflytek.com/space/api/box/stream/download/all/"
        f"{token}/?mount_node_token=dox-private-document&mount_point=docx_image"
    )
    assert request["headers"]["X-CSRFToken"] == "private-csrf"
    assert request["stream"] is True
    serialized_asset = json.dumps(resolution.asset, sort_keys=True)
    assert token not in serialized_asset
    assert request["url"] not in serialized_asset
    assert "private-csrf" not in serialized_asset


def test_image_asset_writer_deduplicates_repeated_resource_tokens(tmp_path: Path) -> None:
    session = FakeSession([FakeResponse(PNG_BYTES)])
    writer = image_writer(tmp_path, session)

    first = writer.resolve(image_reference())
    second = writer.resolve(image_reference())

    assert first.markdown_path == second.markdown_path
    assert first.asset is not None
    assert second.asset is None
    assert len(session.requests) == 1
    assert len(list((tmp_path / "assets" / "docx_1").iterdir())) == 1


def test_image_asset_writer_returns_safe_http_warning_and_removes_partial_file(
    tmp_path: Path,
) -> None:
    token = "boxr-private-token"
    session = FakeSession(
        [
            FakeResponse(PNG_BYTES),
            FakeResponse(
                b"private response body",
                content_type="text/plain",
                status_code=403,
                error_detail=f"{token} private-csrf",
            ),
        ]
    )
    writer = image_writer(tmp_path, session)
    writer.resolve(image_reference("boxr-first-token"))

    resolution = writer.resolve(image_reference(token))

    assert resolution.markdown_path is None
    assert resolution.asset is None
    assert resolution.warning == "image 2 download failed: http_error"
    serialized = json.dumps(resolution.__dict__, sort_keys=True)
    assert token not in serialized
    assert "private response body" not in serialized
    assert "private-csrf" not in serialized
    assert not list((tmp_path / "assets" / "docx_1").glob("*.part"))


def test_image_asset_writer_rejects_non_image_response(tmp_path: Path) -> None:
    session = FakeSession(
        [FakeResponse(b"<html>private</html>", content_type="text/html")]
    )
    writer = image_writer(tmp_path, session)

    resolution = writer.resolve(image_reference())

    assert resolution.markdown_path is None
    assert resolution.warning == "image 1 download failed: mime_error"
    assert not list((tmp_path / "assets" / "docx_1").glob("*"))


def test_image_asset_writer_rejects_invalid_image_magic(tmp_path: Path) -> None:
    session = FakeSession([FakeResponse(b"not-a-png", content_type="image/png")])
    writer = image_writer(tmp_path, session)

    resolution = writer.resolve(image_reference())

    assert resolution.markdown_path is None
    assert resolution.warning == "image 1 download failed: content_error"
    assert not list((tmp_path / "assets" / "docx_1").glob("*"))
