import asyncio
import websockets
import os
import struct

clients = {}       # {websocket: client_id}
positions = {}     # {client_id: (x, y)}

FORMAT = ">ff"     # Big-endian float, float (2 floats = 8 bytes per client)

async def handler(websocket):
	client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
	try:
		print(f"[+] Client connected: {client_id}", flush=True)
		clients[websocket] = client_id
		positions[client_id] = (0.0, 0.0)

		async for message in websocket:
			if isinstance(message, bytes) and len(message) == 8:
				try:
					x, y = struct.unpack(FORMAT, message)
					positions[client_id] = (x, y)
					print(f"[POS] {client_id} => x={x:.2f}, y={y:.2f}", flush=True)
				except Exception as e:
					print(f"[ERR] Binary decode failed from {client_id}: {e}", flush=True)
					continue
			else:
				print(f"[WARN] Ignored non-binary or malformed message from {client_id}", flush=True)
				continue

			# Build binary update for all clients
			update = b''.join(struct.pack(FORMAT, x, y) for x, y in positions.values())

			# Broadcast to all connected clients
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

		# Update remaining clients
		update = b''.join(struct.pack(FORMAT, x, y) for x, y in positions.values())
		for client in clients:
			if client.open:
				await client.send(update)

async def main():
	port = int(os.environ.get("PORT", 10000))
	async with websockets.serve(handler, "0.0.0.0", port):
		print(f"[✔] WebSocket server started on port {port}", flush=True)
		await asyncio.Future()

asyncio.run(main())
