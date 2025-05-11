import asyncio
import websockets

connected = set()

async def handler(websocket):
	connected.add(websocket)
	client_ip = websocket.remote_address[0]
	print(f"[+] Client connected: {client_ip}")
	try:
		async for message in websocket:
			print(f"[{client_ip}] → {message}")
			# Broadcast to all other clients
			for conn in connected:
				if conn != websocket:
					await conn.send(f"[{client_ip}] {message}")
	except websockets.exceptions.ConnectionClosedOK:
		print(f"[-] Client disconnected normally: {client_ip}")
	except websockets.exceptions.ConnectionClosedError:
		print(f"[!] Client disconnected abruptly: {client_ip}")
	finally:
		connected.remove(websocket)
        
