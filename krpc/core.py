from fastapi import APIRouter, Request
from .decoders import Decoder, JsonDecoder, MsgpackDecoder
from .errors import RpcErrorCode, RpcException
from .response import EncoderModelResponse


class Entrypoint(APIRouter):
    def __init__(
            self,
            path: str,
            default_decoder: str = 'application/json',
            decoders: dict[str, Decoder] = None,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.path = path
        self.default_decoder = default_decoder
        self.decoders = decoders or {
            "application/json": JsonDecoder(),
            "application/x-msgpack": MsgpackDecoder()
        }
        self.add_api_route(self.path, self.rpc_endpoint, methods=["POST"])

    async def rpc_endpoint(self, request: Request):
        content_type = request.headers.get("Content-Type", "").lower()
        decoder = self.decoders.get(content_type) or self.default_decoder

        if not decoder:
            return EncoderModelResponse(
                error=RpcException.parse(RpcErrorCode.UNSUPPORTED_CONTENT_TYPE)
            )

        response = await decoder.handle(request, self.routes)
        return response

    def method(self, func):
        self.add_api_route(self.path + "/" + func.__name__, func, methods=["POST"])
        return func
