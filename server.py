import asyncio
import websockets
import os
import struct

clients = {}      # {websocket: client_id}
positions = {}    # {client_id: (x, y)}
client_id_counter = 1

async def handler(websocket):
	global client_id_counter
	client_id = client_id_counter
	client_id_counter += 1

	clients[websocket] = client_id
	positions[client_id] = (0.0, 0.0)

	print(f"[+] Client {client_id} connected", flush=True)

	# Send all existing player positions to the new client
	for cid, (x, y) in positions.items():
		if cid == client_id:
			continue
		initial_packet = struct.pack("<BBff", 0, cid, x, y)  # type=0, id, x, y
		await websocket.send(initial_packet)

	try:
		async for message in websocket:
			if len(message) != 8:
				print("Received msg is not of len 8", flush=True)
				continue  # Invalid packet size

			# Unpack 4-byte float x and y
			x, y = struct.unpack("ff", message)

			# Calculate delta
			old_x, old_y = positions[client_id]
			dx = int((x - old_x) * 100)
			dy = int((y - old_y) * 100)
			positions[client_id] = (x, y)

			# Pack delta update: 1-byte type + 1-byte ID + 2-byte dx + 2-byte dy = 6 bytes
			update = struct.pack("<BBhh", 1, client_id, dx, dy)

			for client in clients:
				if client.open:
					await client.send(update)

	except websockets.exceptions.ConnectionClosed:
		pass

	finally:
		del clients[websocket]
		del positions[client_id]
		print(f"[-] Client {client_id} disconnected", flush=True)

async def main():
	port = int(os.environ.get("PORT", 10000))
	async with websockets.serve(handler, "0.0.0.0", port):
		print(f"[✔] WebSocket server started on port {port}", flush=True)
		await asyncio.Future()

asyncio.run(main())
