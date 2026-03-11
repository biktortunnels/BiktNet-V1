# biktnet.py
import socket
import threading
from Crypto.Cipher import AES
import base64

# ==== CONFIG ====
TRACKER_IP = "127.0.0.1"  # Byt till tracker-serverns IP
TRACKER_PORT = 6000
LOCAL_PORT = 5000
AES_KEY = b'Sixteen byte key'
BLOCK_SIZE = 16

peers = []

# ==== AES Helpers ====
def pad(msg):
    padding_len = BLOCK_SIZE - len(msg) % BLOCK_SIZE
    return msg + chr(padding_len) * padding_len

def unpad(msg):
    padding_len = ord(msg[-1])
    return msg[:-padding_len]

def encrypt(msg):
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(msg).encode())).decode()

def decrypt(msg):
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return unpad(cipher.decrypt(base64.b64decode(msg)).decode())

# ==== P2P Peer Handling ====
def listen_for_peers():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', LOCAL_PORT))
    server.listen()
    while True:
        conn, addr = server.accept()
        peers.append(conn)
        threading.Thread(target=handle_peer, args=(conn,), daemon=True).start()

def handle_peer(conn):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"[Peer] {decrypt(data.decode())}")
    except:
        pass
    peers.remove(conn)
    conn.close()

def connect_to_peer(ip, port):
    for peer in peers:
        if getattr(peer, "remote_ip", None) == ip:
            return  # Already connected
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((ip, int(port)))
        conn.remote_ip = ip
        peers.append(conn)
        threading.Thread(target=handle_peer, args=(conn,), daemon=True).start()
    except:
        print(f"[!] Failed to connect to {ip}:{port}")

# ==== Tracker ====
def get_peers_from_tracker():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TRACKER_IP, TRACKER_PORT))
        data = s.recv(4096).decode()
        s.close()
        if data:
            return data.split(",")
    except:
        pass
    return []

# ==== Chat ====
def send_to_all(msg):
    for peer in peers:
        try:
            peer.send(encrypt(msg).encode())
        except:
            peers.remove(peer)

def main():
    print("[*] Starting BiktNet peer...")
    threading.Thread(target=listen_for_peers, daemon=True).start()

    while True:
        peer_list = get_peers_from_tracker()
        for p in peer_list:
            if p:
                ip, port = p.split(":")
                connect_to_peer(ip, port)
        msg = input()
        if msg.lower() == "exit":
            break
        send_to_all(msg)

if __name__ == "__main__":
    main()