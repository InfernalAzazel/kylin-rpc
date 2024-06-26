from typing import Any
import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport
from pydantic import BaseModel, Field

from krpc import Entrypoint, RpcException, RpcErrorCode, RpcClient

service_url = '/api/v1/msgpack_rpc'
test_url = 'http://test' + service_url
rpc_media_type: str = 'msgpack'


class OperationParams(BaseModel):
    a: int = Field(..., json_schema_extra={"example": 3}, description='A 变量')
    b: int = Field(..., json_schema_extra={"example": 3}, description='B 变量')


class AddParams(BaseModel):
    params: OperationParams
    speak: str = None
    model_config = {
        'method_name': 'add'
    }


class SubtractParams(BaseModel):
    params: OperationParams
    model_config = {
        'method_name': 'subtract'
    }


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    api_v1 = Entrypoint(service_url)

    @app.exception_handler(RpcException)
    async def unicorn_exception_handler(request: Request, exc: RpcException):
        message = api_v1.get_message(request)
        return message.response_handle(error=exc.to_dict)

    @api_v1.method
    async def add(params: OperationParams, speak: str) -> int:
        print(speak)
        if params.a is None or params.b is None:
            raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
        return params.a + params.b

    @api_v1.method
    async def subtract(params: OperationParams) -> int:
        if params.a is None or params.b is None:
            raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
        return params.a - params.b

    app.include_router(api_v1)
    return app


@pytest.mark.asyncio
async def test_add(app: Any):
    transport = ASGITransport(app=app)
    client = RpcClient(url=test_url, rpc_media_type=rpc_media_type, transport=transport)
    params = AddParams(params=OperationParams(a=1, b=2), speak="hello")
    data = await client.call_model_async(params)
    print(f"Response JSON for test_add: {data}")
    assert data['result'] == 3


@pytest.mark.asyncio
async def test_subtract(app: Any):
    transport = ASGITransport(app=app)
    client = RpcClient(url=test_url, rpc_media_type=rpc_media_type, transport=transport)
    params = SubtractParams(params=OperationParams(a=5, b=3))
    data = await client.call_model_async(params)
    print(f"Response JSON for test_subtract: {data}")
    assert data['result'] == 2


@pytest.mark.asyncio
async def test_invalid_params(app: Any):
    transport = ASGITransport(app=app)
    client = RpcClient(url=test_url, rpc_media_type=rpc_media_type, transport=transport)
    params = AddParams(params=OperationParams(a=5, b=3))
    data = await client.call_model_async(params)
    print(f"Response JSON for test_invalid_params: {data}")
    assert data['error']['message'] == RpcException.parse(RpcErrorCode.INVALID_PARAMS)['message']


@pytest.mark.asyncio
async def test_method_not_found(app: Any):
    class MultiplyParams(BaseModel):
        params: OperationParams
        speak: str = None
        model_config = {
            'method_name': 'multiply'
        }

    transport = ASGITransport(app=app)
    client = RpcClient(url=test_url, rpc_media_type=rpc_media_type, transport=transport)
    params = MultiplyParams(params=OperationParams(a=5, b=3))
    data = await client.call_model_async(params)
    print(f"Response JSON for test_method_not_found: {data}")
    assert data['error'] == RpcException.parse(RpcErrorCode.METHOD_NOT_FOUND)
