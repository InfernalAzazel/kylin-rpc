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
