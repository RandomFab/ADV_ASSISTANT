import asyncio
from fastmcp import Client


async def test_order_status():
    async with Client("http://127.0.0.1:8000/sse") as client:
        result = await client.call_tool(
            "get_order_status", {"order_id": "CMD-2024-0002"}
        )
        print(result)


# asyncio.run(test_order_status())


async def test_client_info():
    async with Client("http://127.0.0.1:8000/sse") as client:
        result = await client.call_tool("get_client_info", {"client_name": "robin"})
        print(result)


# asyncio.run(test_client_info())


async def test_stock_level(input_reference: str = None, input_mot_cle: str = None):
    async with Client("http://127.0.0.1:8000/sse") as client:
        params = {}
        if input_reference:
            params["reference"] = input_reference
        if input_mot_cle:
            params["mot_cle"] = input_mot_cle
        result = await client.call_tool("get_stock_level", params)
        print(result)


# asyncio.run(test_stock_level(input_reference="COIL-S235-1.5"))
# asyncio.run(test_stock_level(input_mot_cle="coil acier 3mm"))


async def test_reclamations(input_client_name: str, input_statut: str = None):
    async with Client("http://127.0.0.1:8000/sse") as client:
        params = {"client_name": input_client_name}
        if input_statut:
            params["statut"] = input_statut
        result = await client.call_tool("search_reclamations", params)
        print(result)


# asyncio.run(test_reclamations(input_client_name="Robin S.A.S.", input_statut="ouverte"))


async def test_delivery_estimate(input_order_id: str):
    async with Client("http://127.0.0.1:8000/sse") as client:
        params = {"order_id": input_order_id}
        result = await client.call_tool("get_delivery_estimate", params)
        print(result)


for cmd_id in ["CMD-2024-0078", "CMD-2024-0079", "CMD-2023-0081", "CMD-2024-0114"]:
    asyncio.run(test_delivery_estimate(cmd_id))
