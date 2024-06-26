# krpc

`krpc` 是一个用于在 FastAPI 中实现 RPC（远程过程调用）接口的简单库。它提供了一种方便的方式来定义和处理 RPC 请求和响应。

## 功能

- 简单易用的 RPC 接口定义
- 自动参数验证和错误处理
- 兼容 FastAPI 的路由和依赖注入机制
- 得益于 FastAPI 实现 KrpcAPI 自动文档
- 支持多种解码
- 高性能处理

## 安装

使用 [Poetry](https://python-poetry.org/) 进行安装：

```sh
poetry add kylin-rpc fastapi msgpack
```

或者使用 `pip` 进行安装：

```sh
pip install kylin-rpc fastapi msgpack
```

## 快速开始

在 `examples/basic/main.py` 中创建一个 FastAPI 应用，并定义一些 JSON-RPC 方法：

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.requests import Request
from krpc import Entrypoint, RpcException, RpcErrorCode


class OperationParams(BaseModel):
    a: int = Field(..., json_schema_extra={"example": 3}, description='A 变量')
    b: int = Field(..., json_schema_extra={"example": 3}, description='B 变量')


app = FastAPI(title="Krpc API")
# 创建一个 JSON-RPC 入口点
api_v1 = Entrypoint('/api/v1/jsonrpc')


# 处理全局异常
@app.exception_handler(RpcException)
async def unicorn_exception_handler(request: Request, exc: RpcException):
    message = api_v1.get_message(request)
    return message.response_handle(error=exc.to_dict)


# 定义一个 JSON-RPC 方法 add
@api_v1.method
async def add(params: OperationParams, speak: str) -> int:
    print(speak)
    if params.a is None or params.b is None:
        raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
    return params.a + params.b


# 定义一个 JSON-RPC 方法 subtract
@api_v1.method
async def subtract(params: OperationParams) -> int:
    if params.a is None or params.b is None:
        raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
    return params.a - params.b


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

### 客户端

在 `examples/basic/client.py` 中编写的代码：

```python
import asyncio
from pydantic import BaseModel

from krpc import RpcClient


class OperationParams(BaseModel):
    a: int
    b: int


class AddParams(BaseModel):
    params: OperationParams
    speak: str
    model_config = {
        'method_name': 'add'
    }


async def main():
    rpc_client = RpcClient(url="http://127.0.0.1:8000/api/v1/jsonrpc")

    params = AddParams(params=OperationParams(a=1, b=2), speak="hello")
    response = rpc_client.call_model(params)
    print(f"同步调用结果: {response}")

    response = await rpc_client.call_model_async(params)
    print(f"异步调用结果: {response}")

    response = rpc_client.call('add', {'params': {"a": 1, "b": 2}})
    print(f"同步少参调用结果: {response}")


asyncio.run(main())
```

运行：

```sh
python examples/basic/client.py
```

如果不出意外你会看到类似如下输出:

```shell
同步调用结果: {'id': '8ad9a6cc-d332-4c3f-b6f8-ba734b773a34', 'result': 3, 'error': None}
异步调用结果: {'id': 'da25ef99-5fc4-4e01-8393-b3afad5a0eaa', 'result': 3, 'error': None}
同步少参调用结果: {'id': '16a913d6-8930-4178-ae1c-ce9ee757883e', 'result': None, 'error': {'code': -32602, 'message': 'Invalid params', 'data': 'Missing required parameter: speak'}}
```


## RpcAPI 自动文档

- Swagger UI

![1.png](resources/1.png)

- ReDoc

![2.png](resources/2.png)

## 许可证

MIT License

版权所有（c）2024 Kylin