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

	try:
		async for message in websocket:
			if len(message) != 8:
        print("Received msg is not of len 8", flush=True)
				continue  # Invalid packet size

			# Unpack 4-byte float x and y
			x, y = struct.unpack("ff", message)
			positions[client_id] = (x, y)

			# Pack the update: 2-byte ID + 4-byte x + 4-byte y = 10 bytes
			update = struct.pack("Hff", client_id, x, y)

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
