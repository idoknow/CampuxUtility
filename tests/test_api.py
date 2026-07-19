import asyncio
import json
from pathlib import Path

from src import api
from src.storage import StoredImage


class FakeRenderer:
    def __init__(self, output_path: Path):
        self.output_path = output_path

    async def from_html(self, html: str):
        return "data/rendered_test.html", str(self.output_path.with_suffix(".html"))

    async def html2pic(self, html_file_path, screenshot_options):
        self.output_path.write_bytes(b"jpeg")
        return str(self.output_path)


class FakeStorage:
    def __init__(self):
        self.saved_path: str | None = None

    async def save(self, image_path: str) -> str:
        self.saved_path = image_path
        return "data/rendered_test.jpeg"

    async def get(self, image_id: str):
        if image_id == "rendered_test.jpeg":
            return StoredImage(content=b"jpeg", media_type="image/jpeg")
        return None


def test_generate_json_response_remains_compatible(tmp_path, monkeypatch):
    output_path = tmp_path / "rendered_test.jpeg"
    storage = FakeStorage()
    monkeypatch.setattr(api, "render", FakeRenderer(output_path))
    monkeypatch.setattr(api, "image_storage", storage)

    response = asyncio.run(
        api.text2img(
            api.GenerateRequest(
                html="<html><body>test</body></html>",
                json=True,
            )
        )
    )

    assert response.status_code == 200
    assert json.loads(response.body) == {
        "code": 0,
        "message": "success",
        "data": {"id": "data/rendered_test.jpeg"},
    }
    assert storage.saved_path == str(output_path)


def test_get_image_response_remains_compatible(monkeypatch):
    monkeypatch.setattr(api, "image_storage", FakeStorage())

    response = asyncio.run(api.text2img_image("rendered_test.jpeg"))

    assert response.status_code == 200
    assert response.body == b"jpeg"
    assert response.media_type == "image/jpeg"


def test_get_missing_image_response_remains_compatible(monkeypatch):
    monkeypatch.setattr(api, "image_storage", FakeStorage())

    response = asyncio.run(api.text2img_image("missing.jpeg"))

    assert response.status_code == 404
    assert json.loads(response.body) == {
        "code": 1,
        "message": "file not found",
        "data": {},
    }
