from typing import List, Dict, Any
import httpx
from ..core.exceptions import handle_request_errors

class ChatRoutes:
    def __init__(self, client):
        self.client = client

    def create(self, model: str, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Dict[str, Any]:
        """Synchronous chat completion."""
        payload = {"model": model, "messages": messages, "stream": stream, **kwargs}
        try:
            response = self.client.sync_http.post("/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            handle_request_errors(e)

    async def acreate(self, model: str, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Dict[str, Any]:
        """Asynchronous chat completion."""
        payload = {"model": model, "messages": messages, "stream": stream, **kwargs}
        try:
            response = await self.client.async_http.post("/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            handle_request_errors(e)