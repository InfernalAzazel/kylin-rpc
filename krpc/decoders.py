from typing import Any

import msgpack
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from .errors import JsonRpcException
from .models import JsonRpcRequestModel, JsonRpcErrorModel
from .response import JsonRPCResponse


class Decoder:
    async def decode(self, request: Request) -> Any:
        raise NotImplementedError

    def create_response(self, response: JsonRPCResponse) -> Response:
        raise NotImplementedError

    async def handle(self, request: Request, routes: list) -> JsonRPCResponse:
        try:
            req_data = await self.decode(request)
            req = JsonRpcRequestModel(**req_data)
        except Exception as e:
            return self.create_response(JsonRPCResponse(
                error=JsonRpcErrorModel(code=-32700, message="Parse error").model_dump()
            ))

        response_id = req.id

        for route in routes:
            if route.path == request.url.path + "/" + req.method:
                try:
                    result = await route.endpoint(req.params)
                    return self.create_response(JsonRPCResponse(
                        response_id=response_id, result=result
                    ))
                except JsonRpcException as e:
                    return self.create_response(JsonRPCResponse(
                        response_id=response_id,
                        error=JsonRpcErrorModel(code=e.code, message=e.message, data=e.data).model_dump()
                    ))
                except Exception as e:
                    return self.create_response(JsonRPCResponse(
                        response_id=response_id,
                        error=JsonRpcErrorModel(code=-32603, message="Internal error").model_dump()
                    ))

        return self.create_response(JsonRPCResponse(
            response_id=response_id,
            error=JsonRpcErrorModel(code=-32601, message="Method not found").model_dump()
        ))


class JsonDecoder(Decoder):
    async def decode(self, request: Request) -> Any:
        return await request.json()

    def create_response(self, response: JsonRPCResponse) -> Response:
        return JSONResponse(response)


class MsgpackDecoder(Decoder):
    async def decode(self, request: Request) -> Any:
        return msgpack.unpackb(await request.body(), raw=False)

    def create_response(self, response: JsonRPCResponse) -> Response:
        return Response(
            content=msgpack.packb(response, use_bin_type=True),
            media_type="application/x-msgpack"
        )
