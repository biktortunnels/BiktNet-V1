# biktnet_lan_discovery.py - P2P chat with LAN peer discovery
import socket
import threading
import time

PORT = 5000
DISCOVERY_PORT = 5001  # Separate port for peer discovery
HOST = '0.0.0.0'
clients = []

# =====================
# Handle a connected client
# =====================
def handle_client(conn, addr):
    print(f"[+] Connected: {addr}")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode()
            print(f"[{addr}] {msg}")
            broadcast(msg, conn)
        except:
            break
    conn.close()
    if conn in clients:
        clients.remove(conn)
    print(f"[-] Disconnected: {addr}")

# =====================
# Broadcast to all peers except sender
# =====================
def broadcast(msg, sender):
    for client in clients:
        if client != sender:
            try:
                client.send(msg.encode())
            except:
                pass

# =====================
# Server mode
# =====================
def start_server():
    # Start TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[+] BiktNet listening on {HOST}:{PORT}")

    # Start UDP discovery listener
    threading.Thread(target=listen_discovery, daemon=True).start()

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# =====================
# UDP discovery listener
# =====================
def listen_discovery():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', DISCOVERY_PORT))
    while True:
        data, addr = sock.recvfrom(1024)
        if data.decode() == 'DISCOVER':
            sock.sendto(b'PEER_HERE', addr)

# =====================
# Client mode with LAN discovery
# =====================
def start_client():
    print("[*] Discovering peers on LAN...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Send discovery ping
    sock.sendto(b'DISCOVER', ('<broadcast>', DISCOVERY_PORT))
    peers = []

    # Collect responses
    start_time = time.time()
    while time.time() - start_time < 2:  # 2-second discovery window
        try:
            data, addr = sock.recvfrom(1024)
            if data.decode() == 'PEER_HERE':
                peers.append(addr[0])
        except socket.timeout:
            break

    if not peers:
        print("[!] No peers found.")
        return

    # Show list of discovered peers
    print("Available peers on LAN:")
    for i, ip in enumerate(peers):
        print(f"{i+1}. {ip}")

    choice = int(input("Select peer number to connect: ")) - 1
    target = peers[choice]

    # Connect to selected peer
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((target, PORT))
        print(f"[+] Connected to {target}:{PORT}")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        return

    # Receive thread
    def receive():
        while True:
            try:
                data = client.recv(1024)
                if data:
                    print(f"\n[Peer] {data.decode()}")
            except:
                break

    threading.Thread(target=receive, daemon=True).start()

    # Send messages
    while True:
        msg = input()
        if msg.lower() == 'exit':
            break
        try:
            client.send(msg.encode())
        except:
            print("[!] Failed to send message.")
            break

    client.close()

# =====================
# Main
# =====================
mode = input("Choose mode (server/client): ").strip().lower()
if mode == "server":
    start_server()
elif mode == "client":
    start_client()
else:
    print("Invalid mode")