import os

class Config:
    def __init__(self, base_url: str = None):
        # Prefer the passed URL, fallback to environment variable
        self.BASE_URL = base_url or os.getenv("OLLAMA_NGROK_URL")
        
        if not self.BASE_URL:
            raise ValueError(
                "Base URL is missing. Provide it when initializing the client "
                "or set the 'OLLAMA_NGROK_URL' environment variable."
            )
        
        # Clean up the URL format
        self.BASE_URL = self.BASE_URL.strip().rstrip("/")
        
        # Colab models can be slow to generate the first token, default to 60 seconds
        self.TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "60.0"))