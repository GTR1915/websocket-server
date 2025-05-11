import asyncio
import websockets
import os

clients = set()

async def handler(websocket):
	try:
		print("New client connected")
		clients.add(websocket)
		async for message in websocket:
			print("Received:", message)
			for client in clients:
				if client != websocket:
					await client.send(message)
	except websockets.exceptions.ConnectionClosedOK:
		print("Client closed the connection gracefully")
	except websockets.exceptions.ConnectionClosedError:
		print("Client disconnected abruptly (e.g., lost connection)")
	finally:
		clients.remove(websocket)
		print("Client removed")

async def main():
	port = int(os.environ.get("PORT", 10000))  # Render sets PORT
	async with websockets.serve(handler, "0.0.0.0", port):
		print(f"WebSocket server started on port {port}")
		await asyncio.Future()

asyncio.run(main())
