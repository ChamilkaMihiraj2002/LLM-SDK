import httpx
from typing import Optional
from .core.config import Config
from .routes.chat import ChatRoutes
from .routes.generate import GenerateRoutes

class NeuralBridgeClient:
    def __init__(self, base_url: Optional[str] = None):
        self.config = Config(base_url)
        
        # Bypass ngrok's browser warning page, ensuring direct JSON API access
        headers = {
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/json"
        }
        
        # Maintain persistent connections for better performance
        self.sync_http = httpx.Client(
            base_url=self.config.BASE_URL, 
            headers=headers, 
            timeout=self.config.TIMEOUT
        )
        self.async_http = httpx.AsyncClient(
            base_url=self.config.BASE_URL, 
            headers=headers, 
            timeout=self.config.TIMEOUT
        )
        
        # Register API routes
        self.chat = ChatRoutes(self)
        self.generate = GenerateRoutes(self)

    def close(self):
        """Close synchronous HTTP connections."""
        self.sync_http.close()

    async def aclose(self):
        """Close asynchronous HTTP connections."""
        await self.async_http.aclose()
        
    # --- Context Manager Support for 'with' and 'async with' ---
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()