from typing import Any
import msgpack
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from .errors import RpcException, RpcErrorCode
from .models import RpcRequestModel
from .response import EncoderModelResponse


class Decoder:
    async def decode(self, request: Request) -> Any:
        raise NotImplementedError

    def create_response(self, response: EncoderModelResponse) -> Response:
        raise NotImplementedError

    async def handle(self, request: Request, routes: list) -> EncoderModelResponse:
        try:
            req_data = await self.decode(request)
            req = RpcRequestModel(**req_data)
        except Exception as _:
            return self.create_response(EncoderModelResponse(
                error=RpcException.parse(RpcErrorCode.PARSE_ERROR)
            ))

        response_id = req.id

        for route in routes:
            if route.path == request.url.path + "/" + req.method:
                try:
                    result = await route.endpoint(req.params)
                    return self.create_response(EncoderModelResponse(
                        response_id=response_id, result=result
                    ))
                except Exception as _:
                    return self.create_response(EncoderModelResponse(
                        response_id=response_id,
                        error=RpcException.parse(RpcErrorCode.INVALID_PARAMS)
                    ))

        return self.create_response(EncoderModelResponse(
            response_id=response_id,
            error=RpcException.parse(RpcErrorCode.METHOD_NOT_FOUND)
        ))


class JsonDecoder(Decoder):
    async def decode(self, request: Request) -> Any:
        return await request.json()

    def create_response(self, response: EncoderModelResponse) -> Response:
        return JSONResponse(response)


class MsgpackDecoder(Decoder):
    async def decode(self, request: Request) -> Any:
        return msgpack.unpackb(await request.body(), raw=False)

    def create_response(self, response: EncoderModelResponse) -> Response:
        return Response(
            content=msgpack.packb(response, use_bin_type=True),
            media_type="application/x-msgpack"
        )
