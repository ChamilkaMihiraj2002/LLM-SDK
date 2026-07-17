# LLM-SDK

`LLM-SDK` is a lightweight Python client for calling an LLM service over HTTP. In this repository, the SDK is configured to talk to an Ollama service exposed through an ngrok URL, and it also includes a small FastAPI example app for local testing.

## What is in this repo

- `SDK/` contains the reusable Python SDK.
- `SDK/routes/chat.py` wraps chat-completion style requests.
- `SDK/routes/generate.py` wraps prompt-based text generation requests.
- `tests/run_sync_test.py` shows a synchronous SDK usage example.
- `tests/run_async_api.py` exposes a small FastAPI app that uses the SDK.
- `tests/test_chat_routes.py` contains unit tests for the chat route wrapper.

## Requirements

- Python 3.10+ recommended
- A reachable base URL for your LLM service
- Optional: a `.env` file with your SDK configuration

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The SDK reads its base URL in one of two ways:

1. Pass `base_url` directly to `NeuralBridgeClient(...)`
2. Set `OLLAMA_NGROK_URL` in your environment or `.env` file

Optional environment variable:

- `OLLAMA_TIMEOUT`: request timeout in seconds

Example `.env`:

```env
OLLAMA_NGROK_URL=https://your-ngrok-url.ngrok-free.app
OLLAMA_TIMEOUT=60
```

## SDK routes

The SDK currently wraps these upstream API endpoints:

### 1. `POST /api/chat`

Used by `SDK/routes/chat.py`.

Purpose:
Send a list of chat messages to a chat-capable model.

Payload shape:

```json
{
  "model": "llama3.2:3b",
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "stream": false
}
```

Python usage:

```python
from SDK import NeuralBridgeClient

with NeuralBridgeClient() as client:
    response = client.chat.create(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": "Hello"}],
        stream=False
    )
    print(response)
```

Async usage:

```python
from SDK import NeuralBridgeClient

async with NeuralBridgeClient() as client:
    response = await client.chat.acreate(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": "Hello"}],
        stream=False
    )
    print(response)
```

### 2. `POST /api/generate`

Used by `SDK/routes/generate.py`.

Purpose:
Send a plain prompt to a text-generation endpoint.

Payload shape:

```json
{
  "model": "llama3.2:3b",
  "prompt": "Tell me a short joke about compilers.",
  "stream": false
}
```

Python usage:

```python
from SDK import NeuralBridgeClient

with NeuralBridgeClient() as client:
    response = client.generate.create(
        model="llama3.2:3b",
        prompt="Tell me a short joke about compilers.",
        stream=False
    )
    print(response)
```

## Route exposed inside this repository

This repo also includes a sample FastAPI app exposed through `app.py`.

### 3. `POST /chat`

Purpose:
Accept a message, call the SDK internally, and return the model reply.

Defined in:
`app.py`

Current handler:

- Accepts a JSON body
- Calls `ai_client.chat.acreate(...)`
- Returns:

```json
{
  "route": "chat",
  "model": "llama3.2:3b",
  "reply": "...",
  "raw_response": {}
}
```

Request body:

```json
{
  "message": "Hello",
  "model": "llama3.2:3b",
  "stream": false,
  "options": {}
}
```

### 4. `POST /generate`

Purpose:
Accept a plain prompt, call the SDK generate route internally, and return the model output.

Defined in:
`app.py`

Request body:

```json
{
  "prompt": "Write a short product tagline.",
  "model": "llama3.2:3b",
  "stream": false,
  "options": {}
}
```

Response shape:

```json
{
  "route": "generate",
  "model": "llama3.2:3b",
  "response": "...",
  "raw_response": {}
}
```

### 5. `POST /image/explain`

Purpose:
Send a base64-encoded image plus a prompt to a vision-capable chat endpoint and return the explanation.

Defined in:
`app.py`

Request body:

```json
{
  "image_base64": "BASE64_IMAGE_CONTENT",
  "prompt": "Explain this image.",
  "model": "llama3.2:3b",
  "stream": false,
  "options": {}
}
```

Response shape:

```json
{
  "route": "image_explain",
  "model": "llama3.2:3b",
  "reply": "...",
  "raw_response": {}
}
```

## How to run the SDK

### Option 1: Run the synchronous example

This uses the `generate` route wrapper directly.

```bash
python tests/run_sync_test.py
```

What it does:

- Loads `.env`
- Creates `NeuralBridgeClient()`
- Sends a request to `POST /api/generate`
- Prints the model response

### Option 2: Use the SDK directly in your own script

```python
from SDK import NeuralBridgeClient

with NeuralBridgeClient(base_url="https://your-ngrok-url.ngrok-free.app") as client:
    response = client.chat.create(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": "Explain recursion simply."}]
    )
    print(response)
```

### Option 3: Run the sample FastAPI app

Start the API server:

```bash
python app.py
```

This gives you a simple app-style entrypoint, similar to running a Flask app from a single file.

You can also start it with Uvicorn directly from the project root:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

Backward-compatible test/demo entrypoint:

```bash
python tests/run_async_api.py
```

That starts Uvicorn on:

```text
http://127.0.0.1:8000
```

Available local route:

- `POST http://127.0.0.1:8000/chat`
- `POST http://127.0.0.1:8000/generate`
- `POST http://127.0.0.1:8000/image/explain`

FastAPI docs URLs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Before starting the FastAPI app, make sure your `.env` contains a valid `OLLAMA_NGROK_URL`, because the app creates `NeuralBridgeClient()` on startup.

## How to test with Postman

There are two common things you can test in Postman.

### Test the local FastAPI route

First start the sample API:

```bash
python app.py
```

Then in Postman create a request:

- Method: `POST`
- URL: `http://127.0.0.1:8000/chat`
- Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "message": "Hello from Postman",
  "model": "llama3.2:3b",
  "stream": false,
  "options": {}
}
```

Expected response shape:

```json
{
  "route": "chat",
  "model": "llama3.2:3b",
  "reply": "...",
  "raw_response": {}
}
```

### Test the local `/generate` route

- Method: `POST`
- URL: `http://127.0.0.1:8000/generate`
- Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "prompt": "Write a one-line slogan for a coffee shop.",
  "model": "llama3.2:3b",
  "stream": false,
  "options": {}
}
```

### Test the local `/image/explain` route

- Method: `POST`
- URL: `http://127.0.0.1:8000/image/explain`
- Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "image_base64": "BASE64_IMAGE_CONTENT",
  "prompt": "Explain what is shown in this image.",
  "model": "llama3.2:3b",
  "stream": false,
  "options": {}
}
```

Notes:

- `image_base64` should be the raw base64 content, not a full `data:image/...;base64,...` string.
- Use a vision-capable model for this route if your backend requires one.

### Test the upstream LLM endpoint directly

If you want to bypass the SDK and hit the model service directly in Postman, use your ngrok base URL.

#### Chat endpoint

- Method: `POST`
- URL: `https://your-ngrok-url.ngrok-free.app/api/chat`
- Headers:

```text
Content-Type: application/json
ngrok-skip-browser-warning: true
```

Body:

```json
{
  "model": "llama3.2:3b",
  "messages": [
    {
      "role": "user",
      "content": "Hello from Postman"
    }
  ],
  "stream": false
}
```

#### Generate endpoint

- Method: `POST`
- URL: `https://your-ngrok-url.ngrok-free.app/api/generate`
- Headers:

```text
Content-Type: application/json
ngrok-skip-browser-warning: true
```

Body:

```json
{
  "model": "llama3.2:3b",
  "prompt": "Write a one-line slogan for a coffee shop.",
  "stream": false
}
```

## Running tests

Run the unit tests with:

```bash
python -m unittest tests/test_chat_routes.py
```

## Error handling

The SDK maps common request failures into custom exceptions:

- `NeuralBridgeError`: generic API or HTTP failure
- `ColabTimeoutError`: timeout while waiting for the model response
- `NgrokConnectionError`: connection failure reaching the ngrok URL

Example:

```python
from SDK import NeuralBridgeClient, NeuralBridgeError

try:
    with NeuralBridgeClient() as client:
        result = client.generate.create(
            model="llama3.2:3b",
            prompt="Hello"
        )
        print(result)
except NeuralBridgeError as exc:
    print(f"Request failed: {exc}")
```

## Notes

- The SDK strips any trailing slash from the configured base URL.
- The client sends `ngrok-skip-browser-warning: true` automatically.
- The sample FastAPI app is for local testing and demonstration; the core reusable piece is the `SDK/` package.
