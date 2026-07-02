import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from SDK.core.exceptions import ColabTimeoutError, NeuralBridgeError, NgrokConnectionError
from SDK.routes.chat import ChatRoutes


class ChatRoutesSyncTests(unittest.TestCase):
    def setUp(self):
        self.sync_http = Mock()
        self.client = Mock(sync_http=self.sync_http)
        self.routes = ChatRoutes(self.client)

    def test_create_posts_to_chat_endpoint_with_expected_payload(self):
        messages = [{"role": "user", "content": "Hello"}]
        response_data = {"message": {"role": "assistant", "content": "Hi there"}}

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = response_data
        self.sync_http.post.return_value = response

        result = self.routes.create(
            model="llama3.2:3b",
            messages=messages,
            stream=True,
            temperature=0.2,
        )

        self.sync_http.post.assert_called_once_with(
            "/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": messages,
                "stream": True,
                "temperature": 0.2,
            },
        )
        self.assertEqual(result, response_data)

    def test_create_maps_timeout_errors(self):
        self.sync_http.post.side_effect = httpx.TimeoutException("timed out")

        with self.assertRaises(ColabTimeoutError):
            self.routes.create(model="llama3.2:3b", messages=[])

    def test_create_maps_connection_errors(self):
        self.sync_http.post.side_effect = httpx.ConnectError("connection failed")

        with self.assertRaises(NgrokConnectionError):
            self.routes.create(model="llama3.2:3b", messages=[])

    def test_create_maps_http_status_errors(self):
        request = httpx.Request("POST", "https://example.com/api/chat")
        response = httpx.Response(
            status_code=500,
            request=request,
            text="server error",
        )
        self.sync_http.post.return_value = response

        with self.assertRaises(NeuralBridgeError) as exc:
            self.routes.create(model="llama3.2:3b", messages=[])

        self.assertIn("HTTP Error 500", str(exc.exception))


class ChatRoutesAsyncTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.async_http = Mock()
        self.async_http.post = AsyncMock()
        self.client = Mock(async_http=self.async_http)
        self.routes = ChatRoutes(self.client)

    async def test_acreate_posts_to_chat_endpoint_with_expected_payload(self):
        messages = [{"role": "user", "content": "Hello"}]
        response_data = {"message": {"role": "assistant", "content": "Hi there"}}

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = response_data
        self.async_http.post.return_value = response

        result = await self.routes.acreate(
            model="llama3.2:3b",
            messages=messages,
            stream=False,
            temperature=0.7,
        )

        self.async_http.post.assert_awaited_once_with(
            "/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": messages,
                "stream": False,
                "temperature": 0.7,
            },
        )
        self.assertEqual(result, response_data)

    async def test_acreate_maps_timeout_errors(self):
        self.async_http.post.side_effect = httpx.TimeoutException("timed out")

        with self.assertRaises(ColabTimeoutError):
            await self.routes.acreate(model="llama3.2:3b", messages=[])

    async def test_acreate_maps_connection_errors(self):
        self.async_http.post.side_effect = httpx.ConnectError("connection failed")

        with self.assertRaises(NgrokConnectionError):
            await self.routes.acreate(model="llama3.2:3b", messages=[])

    async def test_acreate_maps_http_status_errors(self):
        request = httpx.Request("POST", "https://example.com/api/chat")
        response = httpx.Response(
            status_code=400,
            request=request,
            text="bad request",
        )
        self.async_http.post.return_value = response

        with self.assertRaises(NeuralBridgeError) as exc:
            await self.routes.acreate(model="llama3.2:3b", messages=[])

        self.assertIn("HTTP Error 400", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
