import asyncio
import websockets
import os

clients = {}

async def handler(websocket):
	client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
	try:
		print(f"[+] Client connected: {client_id}", flush=True)
		clients[websocket] = client_id

		async for message in websocket:
			print(f"[MSG] From {client_id}: {message}", flush=True)
			for client, cid in clients.items():
				if client != websocket:
					await client.send(f"From {client_id}: {message}")
	except websockets.exceptions.ConnectionClosedOK:
		print(f"[✓] Client {client_id} disconnected gracefully", flush=True)
	except websockets.exceptions.ConnectionClosedError:
		print(f"[✗] Client {client_id} disconnected abruptly", flush=True)
	finally:
		clients.pop(websocket, None)
		print(f"[-] Client removed: {client_id}", flush=True)

async def main():
	port = int(os.environ.get("PORT", 10000))  # Render sets PORT
	async with websockets.serve(handler, "0.0.0.0", port):
		print(f"[✔] WebSocket server started on port {port}", flush=True)
		await asyncio.Future()

asyncio.run(main())
