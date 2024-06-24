from typing import Any

import pytest
from fastapi import FastAPI, Request
from httpx import AsyncClient, ASGITransport

from krpc import Entrypoint, RpcException, RpcErrorCode, EncoderModelResponse


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    api_v1 = Entrypoint('/api/v1/jsonrpc')

    @app.exception_handler(RpcException)
    async def unicorn_exception_handler(request: Request, exc: RpcException):
        content_type = request.headers.get("Content-Type", "").lower()
        decoder = api_v1.decoders.get(content_type) or api_v1.default_decoder
        decoder.create_response()
        return EncoderModelResponse(
            error=exc.to_dict
        )

    @api_v1.method
    async def add(params: dict) -> int:
        a = params.get("a")
        b = params.get("b")
        if a is None or b is None:
            raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
        return a + b

    @api_v1.method
    async def subtract(params: dict) -> int:
        a = params.get("a")
        b = params.get("b")
        if a is None or b is None:
            raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
        return a - b

    app.include_router(api_v1)
    return app


@pytest.mark.asyncio
async def test_add(app: Any):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/jsonrpc", json={
            "method": "add",
            "params": {"a": 1, "b": 2},
            "id": 1
        })
        response_json = response.json()
        print(f"Response JSON for test_add: {response_json}")
        assert response.status_code == 200
        assert response_json == {
            "id": 1,
            "result": 3,
            "error": None
        }


@pytest.mark.asyncio
async def test_subtract(app: Any):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/jsonrpc", json={
            "method": "subtract",
            "params": {"a": 5, "b": 3},
            "id": 2
        })
        response_json = response.json()
        print(f"Response JSON for test_subtract: {response_json}")
        assert response.status_code == 200
        assert response_json == {
            "id": 2,
            "result": 2,
            "error": None
        }


@pytest.mark.asyncio
async def test_invalid_params(app: Any):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/jsonrpc", json={
            "method": "add",
            "params": {"a": 1},
            "id": 3,
        })
        assert response.status_code == 200
        response_json = response.json()
        print(f"Response JSON for test_invalid_params: {response_json}")
        assert response_json == {
            "id": 3,
            'result': None,
            "error": RpcException.parse(RpcErrorCode.INVALID_PARAMS)
        }


@pytest.mark.asyncio
async def test_method_not_found(app: Any):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/jsonrpc", json={
            "method": "multiply",
            "params": {"a": 2, "b": 3},
            "id": 4
        })
        assert response.status_code == 200
        response_json = response.json()
        print(f"Response JSON for test_method_not_found: {response_json}")
        assert response_json == {
            "id": 4,
            'result': None,
            "error": RpcException.parse(RpcErrorCode.METHOD_NOT_FOUND)
        }
