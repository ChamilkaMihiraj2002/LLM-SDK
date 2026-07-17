import base64
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app


class AppImageExplainTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_async_http = app.ai_client.async_http
        self.mock_async_http = Mock()
        self.mock_async_http.get = AsyncMock()
        self.mock_async_http.post = AsyncMock()
        app.ai_client.async_http = self.mock_async_http

    def tearDown(self):
        app.ai_client.async_http = self.original_async_http

    async def test_normalize_image_input_downloads_http_url_and_encodes_content(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.content = b"image-bytes"
        self.mock_async_http.get.return_value = response

        result = await app._normalize_image_input("https://example.com/cat.jpg")

        self.mock_async_http.get.assert_awaited_once_with("https://example.com/cat.jpg")
        self.assertEqual(result, base64.b64encode(b"image-bytes").decode("ascii"))

    async def test_handle_image_explain_strips_data_url_prefix_before_forwarding(self):
        upstream_response = Mock()
        upstream_response.raise_for_status.return_value = None
        upstream_response.json.return_value = {
            "message": {"role": "assistant", "content": "A person smiling outdoors."}
        }
        self.mock_async_http.post.return_value = upstream_response

        request = app.ImageExplainRequest(
            image_base64="data:image/png;base64,aGVsbG8=",
            prompt="Explain this image.",
            model="gemma4:12b",
        )

        result = await app.handle_image_explain(request)

        self.mock_async_http.post.assert_awaited_once_with(
            "/api/chat",
            json={
                "model": "gemma4:12b",
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain this image.",
                        "images": ["aGVsbG8="],
                    }
                ],
                "stream": False,
            },
            timeout=app.DEFAULT_VISION_TIMEOUT,
        )
        self.assertEqual(result["reply"], "A person smiling outdoors.")

    async def test_handle_image_explain_surfaces_upstream_400_as_http_exception(self):
        request = httpx.Request("POST", "https://example.com/api/chat")
        upstream_response = httpx.Response(
            status_code=400,
            request=request,
            json={"error": "model does not support images"},
        )
        self.mock_async_http.post.return_value = upstream_response

        payload = app.ImageExplainRequest(
            image_base64=base64.b64encode(b"ok").decode("ascii"),
            prompt="Explain this image.",
            model="gemma4:12b",
        )

        with self.assertRaises(HTTPException) as exc:
            await app.handle_image_explain(payload)

        self.assertEqual(exc.exception.status_code, 400)
        self.assertIn("model does not support images", exc.exception.detail)

    async def test_handle_image_explain_maps_timeout_to_504(self):
        self.mock_async_http.post.side_effect = httpx.ReadTimeout("timed out")

        payload = app.ImageExplainRequest(
            image_base64=base64.b64encode(b"ok").decode("ascii"),
            prompt="Explain this image.",
            model="gemma4:12b",
        )

        with self.assertRaises(HTTPException) as exc:
            await app.handle_image_explain(payload)

        self.assertEqual(exc.exception.status_code, 504)
        self.assertIn("timed out", exc.exception.detail)

    async def test_handle_image_explain_allows_timeout_override_in_options(self):
        upstream_response = Mock()
        upstream_response.raise_for_status.return_value = None
        upstream_response.json.return_value = {
            "message": {"role": "assistant", "content": "A person smiling outdoors."}
        }
        self.mock_async_http.post.return_value = upstream_response

        request = app.ImageExplainRequest(
            image_base64="aGVsbG8=",
            prompt="Explain this image.",
            model="gemma4:12b",
            options={"timeout": 240, "temperature": 0.1},
        )

        await app.handle_image_explain(request)

        self.mock_async_http.post.assert_awaited_once_with(
            "/api/chat",
            json={
                "model": "gemma4:12b",
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain this image.",
                        "images": ["aGVsbG8="],
                    }
                ],
                "stream": False,
                "temperature": 0.1,
            },
            timeout=240.0,
        )


if __name__ == "__main__":
    unittest.main()
