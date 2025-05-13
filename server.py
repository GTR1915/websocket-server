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

	# Step 1: Send welcome packet to new client
	other_players = []
	for cid, (x, y) in positions.items():
		if cid != client_id:
			other_players.append((cid, x, y))

	player_count = len(other_players)

	# Start building welcome packet (type=2, assigned_id, count)
	welcome_packet = struct.pack("<BBB", 2, client_id, player_count)

	# Add each existing player's info to the packet
	for cid, x, y in other_players:
		player_data = struct.pack("<Bff", cid, x, y)
		welcome_packet += player_data

	# Send complete welcome packet to the new client
	await websocket.send(welcome_packet)

	# Step 2: Notify all other clients that a new player has joined
	join_packet = struct.pack("<BBff", 0, client_id, 0.0, 0.0)  # type=0, new_id, x, y

	for client_ws in clients:
		if client_ws != websocket and client_ws.open:
			await client_ws.send(join_packet)

	# Step 3: Start receiving updates from the client
	try:
		async for message in websocket:
			if len(message) != 8:
				print("Received msg is not of len 8", flush=True)
				continue

			# Extract new coordinates
			x, y = struct.unpack("ff", message)

			# Compute delta from old position
			old_x, old_y = positions[client_id]
			dx = int((x - old_x) * 100)
			dy = int((y - old_y) * 100)
			positions[client_id] = (x, y)

			# Pack delta update (type=1, id, dx, dy)
			update_packet = struct.pack("<BBhh", 1, client_id, dx, dy)

			# Broadcast to all connected clients
			for client_ws in clients:
				if client_ws.open:
					await client_ws.send(update_packet)

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
