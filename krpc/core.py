import logging
from fastapi import APIRouter, Request
from .message import Message, JsonMessage, message_management


class Entrypoint(APIRouter):
    def __init__(
            self,
            path: str,
            default_rpc_media_type: str = 'json',
            cust_messages: dict[str, Message] = None,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.path = path
        self.default_rpc_media_type = default_rpc_media_type
        self.messages = cust_messages or message_management
        self.logger = logging.getLogger("fastapi")
        self.add_api_route(self.path, self.rpc_endpoint, methods=["POST"])

    async def rpc_endpoint(self, request: Request):
        message = self.get_message(request)
        return await message.request_handle(request, self.routes)

    @staticmethod
    def get_current_rpc_media_type(request: Request):
        return request.headers.get("X-Krpc-Type", "").lower()

    def get_message(self, request: Request) -> Message:
        current_rpc_media_type = self.get_current_rpc_media_type(request)
        message = self.messages.get(current_rpc_media_type) or self.messages.get(self.default_rpc_media_type)
        if not message:
            self.logger.warning(
                f"krpc No corresponding message decoder found for '{current_rpc_media_type}'. "
                f"Forcing the use of JsonMessage."
            )
            message = JsonMessage()
        return message

    def method(self, func):
        self.add_api_route(self.path + "/" + func.__name__, func, methods=["POST"])
        return func
