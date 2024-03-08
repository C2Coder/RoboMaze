#!/bin/python3
import websockets
import random
import asyncio

server_ip = "localhost"

class ws:
    port = 8001

    async def send_cmd(cmd):
        url = f"ws://{server_ip}:{ws.port}"
        async with websockets.connect(url) as webs:
            # Send a greeting message
            await webs.send(cmd)

# ============= Usage ============= #


while True:
    cmd = input("-> ")
    asyncio.get_event_loop().run_until_complete(ws.send_cmd(f"{cmd}"))
