from typing import Dict, Any
import httpx
from ..core.exceptions import handle_request_errors

class GenerateRoutes:
    def __init__(self, client):
        self.client = client

    def create(self, model: str, prompt: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        """Synchronous text generation."""
        payload = {"model": model, "prompt": prompt, "stream": stream, **kwargs}
        try:
            response = self.client.sync_http.post("/api/generate", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            handle_request_errors(e)

    async def acreate(self, model: str, prompt: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        """Asynchronous text generation."""
        payload = {"model": model, "prompt": prompt, "stream": stream, **kwargs}
        try:
            response = await self.client.async_http.post("/api/generate", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            handle_request_errors(e)