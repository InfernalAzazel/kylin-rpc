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
