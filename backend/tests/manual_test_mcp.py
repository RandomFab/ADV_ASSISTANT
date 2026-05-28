import asyncio
from fastmcp import Client

async def test_order_status():
    async with Client("http://127.0.0.1:8000/sse") as client:
        result = await client.call_tool(
            "get_order_status", 
            {"order_id": "CMD-2024-0002"}
        )
        print(result)

# asyncio.run(test_order_status())

async def test_client_info():
    async with Client("http://127.0.0.1:8000/sse") as client:
        result = await client.call_tool(
            "get_client_info", 
            {"client_name": "robin"}
        )
        print(result)

asyncio.run(test_client_info())