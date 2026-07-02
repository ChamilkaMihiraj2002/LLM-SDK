import httpx

class NeuralBridgeError(Exception):
    """Base exception for all SDK errors."""
    pass

class ColabTimeoutError(NeuralBridgeError):
    """Raised when the Colab instance takes too long to respond."""
    pass

class NgrokConnectionError(NeuralBridgeError):
    """Raised when the ngrok tunnel is invalid, down, or unreachable."""
    pass

def handle_request_errors(e: Exception):
    """Utility to map httpx exceptions to SDK exceptions."""
    if isinstance(e, httpx.TimeoutException):
        raise ColabTimeoutError(f"Colab instance timed out. Check if it's still running. Details: {e}")
    elif isinstance(e, httpx.ConnectError):
        raise NgrokConnectionError(f"Failed to connect to the ngrok tunnel. Details: {e}")
    elif isinstance(e, httpx.HTTPStatusError):
        raise NeuralBridgeError(f"HTTP Error {e.response.status_code}: {e.response.text}")
    else:
        raise NeuralBridgeError(f"An unexpected error occurred: {e}")