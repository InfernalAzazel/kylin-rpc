使用
=====================================


### 创建 FastAPI 应用并定义 JSON-RPC 方法

在 `examples/basic/main.py` 中创建一个 FastAPI 应用，并定义一些 JSON-RPC 方法：

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.requests import Request

from krpc import Entrypoint, RpcException, RpcErrorCode, EncoderModelResponse

app = FastAPI(title="kylin-rpc API")
# 创建一个 JSON-RPC 入口点
api_v1 = Entrypoint('/api/v1/jsonrpc')


# 处理全局异常
@app.exception_handler(RpcException)
async def unicorn_exception_handler(request: Request, exc: RpcException):
    content_type = request.headers.get("Content-Type", "").lower()
    decoder = api_v1.decoders.get(content_type) or api_v1.default_decoder
    decoder.create_response()
    return EncoderModelResponse(
        error=exc.to_dict
    )


class AddParams(BaseModel):
    a: int = Field(..., example=3, description='A 变量')
    b: int = Field(..., example=3, description='B 变量')


# 定义一个 JSON-RPC 方法 add
@api_v1.method
async def add(params: AddParams) -> int:
    a = params.a
    b = params.b
    if a is None or b is None:
        raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
    return a + b


# 定义一个 JSON-RPC 方法 subtract
@api_v1.method
async def subtract(params: AddParams) -> int:
    a = params.a
    b = params.b
    if a is None or b is None:
        raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
    return a - b


# 将 JSON-RPC 入口点注册到 FastAPI 应用中
app.include_router(api_v1)

# 运行应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 运行示例

确保已经安装了依赖，可以运行以下命令来启动服务：

```sh
python examples/basic/main.py
```

现在，你可以发送 JSON-RPC 请求到 `http://localhost:8000/api/v1/jsonrpc` 来调用定义的方法。例如：

**Add 方法请求**
```json
{
  "method": "add",
  "params": {"a": 1, "b": 2},
  "id": 1
}
```

**Subtract 方法请求**
```json
{
  "method": "subtract",
  "params": {"a": 5, "b": 3},
  "id": 2
}
```

### 客户端

在 `examples/basic/client.py` 中编写测试代码：

```python
import asyncio

from httpx import AsyncClient


async def main():
    async with AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/jsonrpc", json={
            "method": "add",
            "params": {"a": 1, "b": 2},
            "id": 1
        })
        response_json = response.json()
        print(f"Response JSON: {response_json}")
        response = await client.post("http://127.0.0.1:8000/api/v1/jsonrpc", json={
            "method": "add",
            "params": {"a": 1},
            "id": 2
        })
        response_json = response.text
        print(f"Response JSON: {response_json}")


asyncio.run(main())
```

运行：

```sh
python examples/basic/client.py
```