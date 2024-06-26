# 使用


### 基本的使用

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

### 自定义消息解码器

在 `examples/cust_messages/cust_messages.py` 例子中继承于 Message 编写自定义 GzipJsonMessage 消息解码器：

```python
import io
import json
from typing import Any, Dict
from krpc import Message, message_management
import gzip


# 自定义加解码器
class GzipJsonMessage(Message):
    rpc_media_type = "gzip-json"

    def decode(self, data: bytes) -> Dict[str, Any] | None:
        """
        使用gzip解压缩数据，并尝试将其反序列化为字典
        :param data: 压缩的字节数据
        :return: 反序列化后的字典
        """
        # 使用gzip解压缩
        buffer = io.BytesIO(data)
        with gzip.GzipFile(fileobj=buffer, mode='rb') as un_gzipped_data:
            data_json_bytes = un_gzipped_data.read()

        # 将解压缩后的字节串反序列化为字典
        data_dict = json.loads(data_json_bytes.decode('utf-8'))
        return data_dict

    def encode(self, data: Dict[str, Any]) -> bytes | None:
        # 将字典转换为JSON格式的字节串
        data_json_bytes = json.dumps(data).encode('utf-8')
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='w') as gzipped_data:
            gzipped_data.write(data_json_bytes)
        return buffer.getvalue()


# 添加 GzipJsonMessage 实例到 message_management 字典中
message_management['gzip-json'] = GzipJsonMessage()
```

在 `examples/cust_messages/main.py` 例子中创建一个 FastAPI 应用，并定义一些 GzipJSON-RPC 方法：

- 

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.requests import Request
from krpc import Entrypoint, RpcException, RpcErrorCode
from cust_messages import message_management


class OperationParams(BaseModel):
    a: int = Field(..., json_schema_extra={"example": 3}, description='A 变量')
    b: int = Field(..., json_schema_extra={"example": 3}, description='B 变量')


app = FastAPI(title="Krpc API")
# 创建一个 GzipJSON-RPC 入口点
api_v1 = Entrypoint(
    '/api/v1/gzip/jsonrpc',
    cust_messages=message_management  # <== 添加我们自定义消息加解码器管理
)


# 处理全局异常
@app.exception_handler(RpcException)
async def unicorn_exception_handler(request: Request, exc: RpcException):
    message = api_v1.get_message(request)
    return message.response_handle(error=exc.to_dict)


# 定义一个 GzipJSON-RPC 方法 add
@api_v1.method
async def add(params: OperationParams, speak: str) -> int:
    print(speak)
    if params.a is None or params.b is None:
        raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
    return params.a + params.b


# 定义一个 GzipJSON-RPC 方法 subtract
@api_v1.method
async def subtract(params: OperationParams) -> int:
    if params.a is None or params.b is None:
        raise RpcException.parse(RpcErrorCode.INVALID_PARAMS)
    return params.a - params.b


# 将 GzipJSON-RPC 入口点注册到 FastAPI 应用中
app.include_router(api_v1)

# 运行应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 运行示例

确保已经安装了依赖，可以运行以下命令来启动服务：

```sh
python examples/cust_messages/main.py
```

现在，你可以发送  GzipJSON-RPC 请求到 `http://localhost:8000/api/v1/gzip/jsonrpc` 来调用定义的方法。例如：

### 客户端

在 `examples/cust_messages/client.py` 中编写的代码：

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
    rpc_client = RpcClient(
        url="http://127.0.0.1:8000/api/v1/gzip/jsonrpc",
        rpc_media_type='gzip-json',  # <== 指定我们自定义的加解码器
    )

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
python examples/cust_messages/client.py
```

如果不出意外你会看到类似如下输出:

```shell
同步调用结果: {'id': '8ad9a6cc-d332-4c3f-b6f8-ba734b773a34', 'result': 3, 'error': None}
异步调用结果: {'id': 'da25ef99-5fc4-4e01-8393-b3afad5a0eaa', 'result': 3, 'error': None}
同步少参调用结果: {'id': '16a913d6-8930-4178-ae1c-ce9ee757883e', 'result': None, 'error': {'code': -32602, 'message': 'Invalid params', 'data': 'Missing required parameter: speak'}}
```

### 消息编码器默认支持

- `krpc` 内置支持以下几种消息编码器
- 允许编码器自定义，以满足多样化的数据传输和存储需求：

| 编码器名称       | 媒体类型      | 特点           | 适用场景            |
|-------------|-----------|--------------|-----------------|
| JSON        | `json`    | 简洁、可读性强、广泛支持 | 数据交换、配置文件、日志记录  |
| MessagePack | `msgpack` | 高效、体积小、速度快   | 性能关键型应用、移动应用、游戏 |
