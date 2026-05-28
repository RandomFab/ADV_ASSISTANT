import asyncio
from fastmcp import Client

async def test():
    async with Client("http://127.0.0.1:8000/sse") as client:
        result = await client.call_tool(
            "get_order_status", 
            {"order_id": "CMD-2024-0002"}
        )
        print(result)

asyncio.run(test())