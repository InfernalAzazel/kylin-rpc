import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from krpc import Entrypoint, JsonRpcException


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    api_v1 = Entrypoint('/api/v1/jsonrpc')

    @api_v1.method
    async def add(params: dict) -> int:
        a = params.get("a")
        b = params.get("b")
        if a is None or b is None:
            raise JsonRpcException(code=-32602, message="Invalid params")
        return a + b

    @api_v1.method
    async def subtract(params: dict) -> int:
        a = params.get("a")
        b = params.get("b")
        if a is None or b is None:
            raise JsonRpcException(code=-32602, message="Invalid params")
        return a - b

    app.include_router(api_v1)
    return app


@pytest.mark.asyncio
async def test_add(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/jsonrpc", json={
            "jsonrpc": "2.0",
            "method": "add",
            "params": {"a": 1, "b": 2},
            "id": 1
        })
        response_json = response.json()
        print(f"Response JSON for test_add: {response_json}")
        assert response.status_code == 200
        assert response_json == {
            "jsonrpc": "2.0",
            "id": 1,
            "result": 3,
            "error": None
        }


@pytest.mark.asyncio
async def test_subtract(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/jsonrpc", json={
            "jsonrpc": "2.0",
            "method": "subtract",
            "params": {"a": 5, "b": 3},
            "id": 2
        })
        response_json = response.json()
        print(f"Response JSON for test_subtract: {response_json}")
        assert response.status_code == 200
        assert response_json == {
            "jsonrpc": "2.0",
            "id": 2,
            "result": 2,
            "error": None
        }


@pytest.mark.asyncio
async def test_invalid_params(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/jsonrpc", json={
            "jsonrpc": "2.0",
            "method": "add",
            "params": {"a": 1},
            "id": 3,
        })
        assert response.status_code == 200
        response_json = response.json()
        print(f"Response JSON for test_invalid_params: {response_json}")
        assert response_json == {
            "jsonrpc": "2.0",
            "id": 3,
            "error": {
                "code": -32602,
                "message": "Invalid params",
                "data": None
            }
        }


@pytest.mark.asyncio
async def test_method_not_found(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/jsonrpc", json={
            "jsonrpc": "2.0",
            "method": "multiply",
            "params": {"a": 2, "b": 3},
            "id": 4
        })
        assert response.status_code == 200
        response_json = response.json()
        print(f"Response JSON for test_method_not_found: {response_json}")
        assert response_json == {
            "jsonrpc": "2.0",
            "id": 4,
            "error": {
                "code": -32601,
                "message": "Method not found",
                "data": None
            }
        }
