from contextlib import asynccontextmanager
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from SDK import NeuralBridgeClient

load_dotenv(PROJECT_ROOT / ".env")

ai_client = NeuralBridgeClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await ai_client.aclose()

app = FastAPI(title="AI Service Gateway", lifespan=lifespan)

@app.post("/chat")
async def handle_chat(message: str):
    response = await ai_client.chat.acreate(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": message}]
    )
    return {"reply": response["message"]["content"]}

if __name__ == "__main__":
    uvicorn.run("run_async_api:app", host="127.0.0.1", port=8000, reload=False)
