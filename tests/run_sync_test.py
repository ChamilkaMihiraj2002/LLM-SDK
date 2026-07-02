import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from SDK import NeuralBridgeClient

# Load the environment variables from the .env file
load_dotenv(PROJECT_ROOT / ".env")

# Client automatically picks up OLLAMA_NGROK_URL from the environment
with NeuralBridgeClient() as ai_client:
    print("Sending request to Colab via ngrok...")
    response = ai_client.generate.create(
        model="llama3.2:3b", 
        prompt="Tell me a short joke about compilers."
    )
    print("\nResponse from LLM:")
    print(response["response"])
