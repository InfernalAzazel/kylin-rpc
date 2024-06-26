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
