import asyncio
import websockets
import json
import requests
import time

WS_URI = "ws://127.0.0.1:8000/ws?project=demo"
UPLOAD_URL = "http://127.0.0.1:8000/upload"
API_KEY = "dev-key-1"

async def ws_and_upload():
    async with websockets.connect(WS_URI) as ws:
        print("WS connected:", WS_URI)
        # start upload in background after a short delay to ensure WS subscription is active
        await asyncio.sleep(1.0)
        # create a small file content and upload via requests (synchronous)
        files = {'file': ('hello_from_combined_test.txt', b'hello combined')}
        headers = {'Authorization': f'Bearer {API_KEY}'}
        print("Starting upload...")
        r = requests.post(UPLOAD_URL, files=files, data={'project':'demo','path':'hello_from_combined_test.txt','client_id':'tester'}, headers=headers)
        print("Upload HTTP:", r.status_code)
        try:
            print("Upload response:", json.dumps(r.json(), indent=2))
        except Exception:
            print("Upload response text:", r.text)
        # Now wait for a notification for up to 10 seconds
        ws_recv_task = asyncio.create_task(ws.recv())
        try:
            notif = await asyncio.wait_for(ws_recv_task, timeout=10.0)
            try:
                obj = json.loads(notif)
            except Exception:
                obj = notif
            print("WS notification received:", obj)
        except asyncio.TimeoutError:
            print("No WS notification received within 10s")

if __name__ == "__main__":
    asyncio.run(ws_and_upload())