import socket
import threading
import os
import time
import re

# Render настройки
port = int(os.environ.get("PORT", 404))
host = '0.0.0.0'

print(f" Starting server on port {port}")

clients = []
banned_ips = []
banned_nicks = []
muted_clients = []
muted_nicks = []
flood_detection = {}
bad_words = ['root']
admins = ['admin']


def is_flooding(ip_address):
    current_time = time.time()
    if ip_address not in flood_detection:
        flood_detection[ip_address] = {'count': 0, 'last_reset': current_time}

    flood_data = flood_detection[ip_address]
    if current_time - flood_data['last_reset'] > 10:
        flood_data['count'] = 0
        flood_data['last_reset'] = current_time

    flood_data['count'] += 1
    return flood_data['count'] > 10


def is_admin(nickname):
    return nickname.lower() in [admin.lower() for admin in admins]


def broadcast_message(message, sender_socket):
    for client in clients[:]:
        if client[0] != sender_socket:
            try:
                client[0].send(message.encode('utf-8'))
            except:
                clients.remove(client)


def handle_client(client_socket, address):
    global clients, muted_clients, banned_nicks

    if address[0] in banned_ips:
        client_socket.send("[SERVER] Your IP is banned".encode('utf-8'))
        client_socket.close()
        return

    try:
        nickname = client_socket.recv(1024).decode('utf-8')
        if not nickname:
            client_socket.close()
            return

        if nickname in banned_nicks:
            client_socket.send("[SERVER] You're fired".encode('utf-8'))
            client_socket.close()
            return

        client_info = (client_socket, nickname, address)
        clients.append(client_info)

        if nickname in muted_nicks:
            muted_clients.append(client_socket)
            client_socket.send("[SERVER] You have been muted!".encode('utf-8'))

        print(f'[+] new connection: {nickname} ({address})')
        broadcast_message(f"[SERVER] {nickname} joined!", client_socket)

        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            if client_socket in muted_clients:
                client_socket.send("[SERVER] You are muted!".encode('utf-8'))
                continue

            if is_flooding(address[0]):
                muted_clients.append(client_socket)
                client_socket.send("[SERVER] You have been muted for flooding!".encode('utf-8'))
                continue

            print(f"{nickname}: {message}")
            broadcast_message(f"[{nickname}] {message}", client_socket)

    except Exception as e:
        print(f'[-] error with client {address}: {e}')
    finally:
        for client in clients[:]:
            if client[0] == client_socket:
                clients.remove(client)
                print(f'[-] client disconnected: {client[1]}')
                broadcast_message(f"[SERVER] {client[1]} leaved!", client_socket)
                break

        if client_socket in muted_clients:
            muted_clients.remove(client_socket)

        if address[0] in flood_detection:
            del flood_detection[address[0]]

        client_socket.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((host, port))
        server.listen(5)
        print(f"Server started on {host}:{port}")

        while True:
            client_socket, address = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address)
            )
            client_thread.daemon = True
            client_thread.start()


    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
