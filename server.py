import asyncio
import websockets
import os
import struct
import time

'''
Message Format Definitions:
- Type 0: New player joined. Format = BBii (10 bytes)
- Type 1: Delta update. Format = B + Bhh + Bhh + ... (5n+2 bytes)
- Type 2: Welcome message for new joiner. Format = BBB + Bii + Bii + ...
- Type 3: Full-state sync (periodic). Format = BB + Bii + Bii + ...
'''

clients = {}       # {websocket: client_id}
positions = {}     # {client_id: (x, y)}
client_id_counter = 1
TICK_RATE = 0.04   # 40 ms per tick
FULL_SYNC_INTERVAL = 2.0  # seconds

# Handle each connected client
async def handler(websocket):
	global client_id_counter
	client_id = client_id_counter
	client_id_counter += 1

	clients[websocket] = client_id
	positions[client_id] = (0, 0)

	print(f"[+] Client {client_id} connected", flush=True)

	# Prepare and send welcome packet (type 2)
	other_players = [(cid, x, y) for cid, (x, y) in positions.items() if cid != client_id]
	welcome_packet = struct.pack("<BBB", 2, client_id, len(other_players))
	for cid, x, y in other_players:
		welcome_packet += struct.pack("<Bii", cid, x, y)
	await websocket.send(welcome_packet)

	# Notify others about this new player (type 0)
	join_packet = struct.pack("<BBii", 0, client_id, 0, 0)
	for ws in clients:
		if ws != websocket and ws.open:
			await ws.send(join_packet)

	try:
		# Listen to this client for position updates
		async for message in websocket:
			if len(message) != 8:
				print("[WARN] Invalid message length:", len(message))
				continue

			try:
				x, y = struct.unpack("ii", message)
			except:
				print("[ERR] Malformed data from", client_id)
				continue

			# Update position and store delta
			old_x, old_y = positions[client_id]
			dx, dy = x - old_x, y - old_y
			positions[client_id] = (x, y)

	except websockets.exceptions.ConnectionClosed:
		pass
	finally:
		# Cleanup on disconnect
		print(f"[-] Client {client_id} disconnected", flush=True)
		del clients[websocket]
		del positions[client_id]

# Broadcast loop: send delta updates every tick, and full-state sync every 2s
async def broadcast_loop():
	last_sync_time = time.time()
	last_positions = positions.copy()

	while True:
		await asyncio.sleep(TICK_RATE)
		delta_packet = struct.pack("<B", 1)

		# Create delta packets (type 1) for all clients
		for cid, (x, y) in positions.items():
			old_x, old_y = last_positions.get(cid, (x, y))
			dx, dy = x - old_x, y - old_y
			if dx != 0 or dy != 0:
				delta_packet += struct.pack("<Bhh", cid, dx, dy)
				last_positions[cid] = (x, y)

		# Send delta updates to all clients
		for ws in clients:
			if ws.open:
				await ws.send(delta_packet)

		# Send full state sync every 2 seconds, msg type 3
		if time.time() - last_sync_time >= FULL_SYNC_INTERVAL:
			sync_packet = struct.pack("<BB", 3, len(positions))
			for cid, (x, y) in positions.items():
				sync_packet += struct.pack("<Bii", cid, x, y)
			for ws in clients:
				if ws.open:
					await ws.send(sync_packet)
			last_sync_time = time.time()
			print("[SYNC] Full-state sync sent")

# Main server entry
async def main():
	port = int(os.environ.get("PORT", 10000))
	async with websockets.serve(handler, "0.0.0.0", port):
		print(f"[✔] WebSocket server started on port {port}", flush=True)
		await broadcast_loop()

asyncio.run(main())
