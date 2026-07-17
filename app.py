import base64
import binascii
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from SDK import NeuralBridgeClient

load_dotenv()

ai_client = NeuralBridgeClient()
DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_VISION_TIMEOUT = max(ai_client.config.TIMEOUT, 180.0)


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to send to the chat model.")
    model: str = Field(DEFAULT_MODEL, description="Model name to use.")
    stream: bool = Field(False, description="Whether the upstream API should stream.")
    options: dict[str, Any] = Field(default_factory=dict, description="Additional upstream parameters.")


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt to send to the text generation endpoint.")
    model: str = Field(DEFAULT_MODEL, description="Model name to use.")
    stream: bool = Field(False, description="Whether the upstream API should stream.")
    options: dict[str, Any] = Field(default_factory=dict, description="Additional upstream parameters.")


class ImageExplainRequest(BaseModel):
    image_base64: str = Field(
        ...,
        description="Raw base64 image content, a base64 data URL, or a direct http/https image URL.",
    )
    prompt: str = Field("Explain this image.", description="Instruction for the vision-capable model.")
    model: str = Field(DEFAULT_MODEL, description="Vision-capable model name to use.")
    stream: bool = Field(False, description="Whether the upstream API should stream.")
    options: dict[str, Any] = Field(default_factory=dict, description="Additional upstream parameters.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await ai_client.aclose()


app = FastAPI(title="AI Service Gateway", lifespan=lifespan)


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_base64_payload(value: str) -> str:
    normalized = "".join(value.strip().split())
    if not normalized:
        raise HTTPException(status_code=400, detail="Image payload cannot be empty.")

    try:
        base64.b64decode(normalized, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Image input must be raw base64, a base64 data URL, or an http/https image URL.",
        ) from exc

    return normalized


async def _normalize_image_input(image_value: str) -> str:
    stripped = image_value.strip()

    if stripped.startswith("data:"):
        header, separator, encoded = stripped.partition(",")
        if separator != "," or ";base64" not in header:
            raise HTTPException(
                status_code=400,
                detail="Data URLs must include a base64-encoded payload.",
            )
        return _validate_base64_payload(encoded)

    if _is_http_url(stripped):
        try:
            response = await ai_client.async_http.get(stripped)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to download image URL: upstream returned {exc.response.status_code}.",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=400,
                detail="Unable to download image URL.",
            ) from exc

        return base64.b64encode(response.content).decode("ascii")

    return _validate_base64_payload(stripped)


def _upstream_error_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        return text or "No error details returned by upstream service."

    if isinstance(data, dict):
        for key in ("error", "detail", "message"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value

    return str(data)


@app.post("/chat")
async def handle_chat(request: ChatRequest):
    response = await ai_client.chat.acreate(
        model=request.model,
        messages=[{"role": "user", "content": request.message}],
        stream=request.stream,
        **request.options,
    )
    return {
        "route": "chat",
        "model": request.model,
        "reply": response["message"]["content"],
        "raw_response": response,
    }


@app.post("/generate")
async def handle_generate(request: GenerateRequest):
    response = await ai_client.generate.acreate(
        model=request.model,
        prompt=request.prompt,
        stream=request.stream,
        **request.options,
    )
    return {
        "route": "generate",
        "model": request.model,
        "response": response.get("response"),
        "raw_response": response,
    }


@app.post("/image/explain")
async def handle_image_explain(request: ImageExplainRequest):
    normalized_image = await _normalize_image_input(request.image_base64)
    request_options = dict(request.options)
    timeout = float(request_options.pop("timeout", DEFAULT_VISION_TIMEOUT))
    payload = {
        "model": request.model,
        "messages": [
            {
                "role": "user",
                "content": request.prompt,
                "images": [normalized_image],
            }
        ],
        "stream": request.stream,
        **request_options,
    }
    try:
        response = await ai_client.async_http.post("/api/chat", json=payload, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail=(
                "Upstream image explain request timed out. "
                f"Try a smaller image, a faster vision model, or increase `options.timeout` above {timeout} seconds."
            ),
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to reach upstream image service: {exc}",
        ) from exc
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Upstream rejected image explain request: {_upstream_error_detail(exc.response)}",
        ) from exc

    data = response.json()
    return {
        "route": "image_explain",
        "model": request.model,
        "reply": data["message"]["content"],
        "raw_response": data,
    }


def main():
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
