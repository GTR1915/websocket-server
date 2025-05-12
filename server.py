import asyncio
import websockets
import os
import json

clients = {}           # {websocket: client_id}
positions = {}         # {client_id: {"x": ..., "y": ...}}

async def handler(websocket):
	client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
	try:
		print(f"[+] Client connected: {client_id}", flush=True)
		clients[websocket] = client_id
		positions[client_id] = {"x": 0, "y": 0}  # Default position

		async for message in websocket:
			print(f"[MSG] From {client_id}: {message}", flush=True)
			
			try:
				data = json.loads(message)
				positions[client_id] = {"x": data["x"], "y": data["y"]}
			except Exception as e:
				print(f"[ERR] Invalid data from {client_id}: {e}", flush=True)
				continue

			update = json.dumps(positions)

			for client in clients:
				if client.open:
					await client.send(update)

	except websockets.exceptions.ConnectionClosedOK:
		print(f"[✓] Client {client_id} disconnected gracefully", flush=True)
	except websockets.exceptions.ConnectionClosedError:
		print(f"[✗] Client {client_id} disconnected abruptly", flush=True)
	finally:
		clients.pop(websocket, None)
		positions.pop(client_id, None)
		print(f"[-] Client removed: {client_id}", flush=True)

		# Notify remaining clients
		update = json.dumps(positions)
		for client in clients:
			if client.open:
				await client.send(update)

async def main():
	port = int(os.environ.get("PORT", 10000))  # Render sets PORT
	async with websockets.serve(handler, "0.0.0.0", port):
		print(f"[✔] WebSocket server started on port {port}", flush=True)
		await asyncio.Future()

asyncio.run(main())
