# ws_test.py
import asyncio, websockets, json

async def run():
    uri = "ws://127.0.0.1:8000/ws?project=demo"
    async with websockets.connect(uri) as ws:
        print("Connected to websocket for project=demo. Waiting for messages...")
        while True:
            msg = await ws.recv()
            print("WS msg:", msg)

asyncio.get_event_loop().run_until_complete(run())