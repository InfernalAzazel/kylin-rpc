from fastapi import FastAPI
from pydantic import BaseModel, Field

from krpc import Entrypoint, JsonRpcException

app = FastAPI(title="kylin-rpc API")

# 创建一个 JSON-RPC 入口点
api_v1 = Entrypoint('/api/v1/jsonrpc')


class AddParams(BaseModel):
    a: int = Field(..., example=3, description='A 变量')
    b: int = Field(..., example=3, description='B 变量')


# 定义一个 JSON-RPC 方法 add
@api_v1.method
async def add(params: AddParams) -> int:
    a = params.a
    b = params.b
    if a is None or b is None:
        raise JsonRpcException(code=-32602, message="Invalid params")
    return a + b


# 定义一个 JSON-RPC 方法 subtract
@api_v1.method
async def subtract(params: AddParams) -> int:
    a = params.a
    b = params.b
    if a is None or b is None:
        raise JsonRpcException(code=-32602, message="Invalid params")
    return a - b


# 将 JSON-RPC 入口点注册到 FastAPI 应用中
app.include_router(api_v1)

# 运行应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
