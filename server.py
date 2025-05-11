import asyncio
import websockets
import os

clients = set()

async def handler(websocket):
	try:
		print("New client connected", flush=True)
		clients.add(websocket)
		async for message in websocket:
			print("Received:", message, flush=True)
			for client in clients:
				if client != websocket:
					await client.send(message)
	except websockets.exceptions.ConnectionClosedOK:
		print("Client closed the connection gracefully", flush=True)
	except websockets.exceptions.ConnectionClosedError:
		print("Client disconnected abruptly (e.g., lost connection)", flush=True)
	finally:
		clients.remove(websocket)
		print("Client removed", flush=True)

async def main():
	port = int(os.environ.get("PORT", 10000))  # Render sets PORT
	async with websockets.serve(handler, "0.0.0.0", port):
		print(f"WebSocket server started on port {port}", flush=True)
		await asyncio.Future()

asyncio.run(main())
