import inspect
import json
from typing import Any, Dict, Union, get_type_hints
import msgpack
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from .errors import RpcException, RpcErrorCode
from .models import RpcRequestModel, RpcResponseModel


class Message:
    rpc_media_type: str | None = None

    def decode(self, data: bytes) -> Dict[str, Any] | None:
        raise NotImplementedError

    def encode(self, data: Dict[str, Any]) -> bytes | None:
        raise NotImplementedError

    async def request_handle(self, request: Request, routes: list) -> Response:
        try:

            req_data = self.decode(await request.body())
            req = RpcRequestModel(**req_data)
        except Exception as _:
            return self.response_handle(
                error=RpcException.parse(RpcErrorCode.PARSE_ERROR)
            )

        response_id = req.id

        for route in routes:
            if route.path == request.url.path + "/" + req.method:
                try:
                    # 获取方法的参数名称和类型
                    signature = inspect.signature(route.endpoint)
                    parameters = signature.parameters

                    # 构造参数字典
                    kwargs = {}
                    for param_name, param in parameters.items():
                        if param_name in req.params:
                            param_type = get_type_hints(route.endpoint).get(param_name, Any)
                            if issubclass(param_type, BaseModel):
                                kwargs[param_name] = param_type(**req.params[param_name])
                            else:
                                kwargs[param_name] = req.params[param_name]
                        elif param.default == inspect.Parameter.empty:
                            # 没有按照填写必须的参数数据
                            return self.response_handle(
                                response_id=response_id, error=RpcException.parse(
                                    RpcErrorCode.INVALID_PARAMS,
                                    f"Missing required parameter: {param_name}"
                                )
                            )

                    result = await route.endpoint(**kwargs)
                    return self.response_handle(
                        response_id=response_id, result=result
                    )
                except Exception as _:
                    return self.response_handle(
                        response_id=response_id,
                        error=RpcException.parse(RpcErrorCode.INVALID_PARAMS)
                    )

        return self.response_handle(
            response_id=response_id,
            error=RpcException.parse(RpcErrorCode.METHOD_NOT_FOUND)
        )

    def response_handle(
            self,
            response_id: Union[str, int, None] = None,
            result: Any = None,
            error: Union[Dict[str, Any], Any, None] = None,
    ) -> Response:

        jsonable_data = jsonable_encoder(
            RpcResponseModel(id=response_id, result=result, error=error)
        )
        content = self.encode(jsonable_data)
        return Response(
            content,
            media_type=self.rpc_media_type,
        )


class JsonMessage(Message):
    rpc_media_type = "json"

    def decode(self, data: bytes) -> Dict[str, Any] | None:
        return json.loads(data)

    def encode(self, data: dict) -> bytes | None:
        json_str = json.dumps(data)
        bytes_data = json_str.encode('utf-8')
        return bytes_data


class MsgpackMessage(Message):
    rpc_media_type = "msgpack"

    def decode(self, data: bytes) -> Dict[str, Any] | None:
        return msgpack.unpackb(data, raw=False)

    def encode(self, data: Dict[str, Any]) -> bytes | None:
        return msgpack.packb(data, use_bin_type=True)


message_management: dict[str, Message] = {
    "json": JsonMessage(),
    "msgpack": MsgpackMessage(),
}
