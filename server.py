import socket
import threading
import os

clients = []  # Список клиентов (socket, nickname, address)
banned_ips = []  # Список забаненных IP-адресов
banned_nicks = []  # Список забаненных никнеймов
muted_clients = []  # Список замьюченных клиентов (socket)
muted_nicks = []  # Список замьюченных никнеймов

host = '0.0.0.0'
port = int(os.environ.get("PORT", 404))

def handle_client(client_socket, address):
    global clients, muted_clients, banned_nicks

    # не забанен ли IP
    if address[0] in banned_ips:
        client_socket.send("[SERVER] Your IP is banned".encode('utf-8'))
        client_socket.close()
        return

    try:
        # никнейм при подключении
        nickname = client_socket.recv(1024).decode('utf-8')
        if not nickname:
            client_socket.close()
            return

        # не забанен ли никнейм
        if nickname in banned_nicks:
            client_socket.send("[SERVER] You`re fired".encode('utf-8'))
            client_socket.close()
            return


        client_info = (client_socket, nickname, address)
        clients.append(client_info)

        # не замьючен ли никнейм
        if nickname in muted_nicks:
            muted_clients.append(client_socket)
            client_socket.send("[SERVER] You have been muted!".encode('utf-8'))

        print(f'[+] new connection: {nickname} ({address})')
        broadcast_message(f"[SERVER] {nickname} joined!", client_socket)

        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            # Проверяем, не замьючен ли клиент
            if client_socket in muted_clients:
                client_socket.send("[SERVER] You are muted and cannot send messages!".encode('utf-8'))
                continue

            # Находим никнейм отправителя
            sender_nickname = nickname
            for client in clients:
                if client[0] == client_socket:
                    sender_nickname = client[1]
                    break

            print(f"{sender_nickname} {address}: {message}")
            broadcast_message(f"[{sender_nickname}] {message}", client_socket)

    except Exception as e:
        print(f'[-] error with client {address}: {e}')
    finally:
        # Удаляем клиента из списка и уведомляем остальных
        for client in clients[:]:
            if client[0] == client_socket:
                clients.remove(client)
                print(f'[-] client disconnected: {client[1]} ({address})')
                broadcast_message(f"[SERVER] {client[1]} leaved!", client_socket)
                break
        # Удаляем из списка мьютов
        if client_socket in muted_clients:
            muted_clients.remove(client_socket)
        client_socket.close()


def broadcast_message(message, sender_socket):
    """Отправляет сообщение всем клиентам кроме отправителя"""
    for client in clients[:]:
        if client[0] != sender_socket:
            try:
                client[0].send(message.encode('utf-8'))
            except:
                # Удаляем нерабочего клиента
                clients.remove(client)


def list_clients():
    """Показывает список подключенных клиентов"""
    if not clients:
        print("no clients")
    else:
        print("clients:")
        for i, (socket, nickname, address) in enumerate(clients, 1):
            status = "muted" if socket in muted_clients else "active"
            print(f"{i}. {nickname} ({address[0]}:{address[1]}) - {status}")


def ban_ip(ip_address):
    """Бан клиента по IP адресу"""
    global banned_ips, clients

    # Добавляем IP в список банов
    if ip_address not in banned_ips:
        banned_ips.append(ip_address)
        print(f"[+] IP {ip_address} banned")


    for client in clients[:]:
        if client[2][0] == ip_address:
            try:
                client[0].send("[SERVER] You have been banned!".encode('utf-8'))
                client[0].close()
            except:
                pass
            clients.remove(client)
            print(f"[-] Disconnected banned client: {client[1]}")


def unban_ip(ip_address):
    """Разбан клиента по IP адресу"""
    global banned_ips
    if ip_address in banned_ips:
        banned_ips.remove(ip_address)
        print(f"[+] IP {ip_address} unbanned")


def ban_nick(nickname):
    """Бан клиента по никнейму"""
    global banned_nicks, clients

    # Добавляем никнейм в список банов
    if nickname not in banned_nicks:
        banned_nicks.append(nickname)
        print(f"[+] Nickname {nickname} banned")

    # Отключаем всех клиентов с этим ником
    for client in clients[:]:
        if client[1] == nickname:
            try:
                client[0].send("[SERVER] You have been banned!".encode('utf-8'))
                client[0].close()
            except:
                pass
            clients.remove(client)
            print(f"[-] Disconnected banned client: {client[1]}")


def unban_nick(nickname):
    """Разбан клиента по нику"""
    global banned_nicks
    if nickname in banned_nicks:
        banned_nicks.remove(nickname)
        print(f"[+] Nickname {nickname} unbanned")


def mute_ip(ip_address):
    """Мут клиента по IP адресу"""
    global muted_clients
    muted_count = 0

    for client in clients:
        if client[2][0] == ip_address:
            if client[0] not in muted_clients:
                muted_clients.append(client[0])
                try:
                    client[0].send("[SERVER] You have been muted!".encode('utf-8'))
                except:
                    pass
                muted_count += 1
                print(f"[+] Muted: {client[1]} ({ip_address})")

    if muted_count == 0:
        print(f"[-] No clients found with IP: {ip_address}")


def unmute_ip(ip_address):
    """Размут клиента по IP адресу"""
    global muted_clients
    unmuted_count = 0

    for client in clients:
        if client[2][0] == ip_address:
            if client[0] in muted_clients:
                muted_clients.remove(client[0])
                try:
                    client[0].send("[SERVER] You have been unmuted!".encode('utf-8'))
                except:
                    pass
                unmuted_count += 1
                print(f"[+] Unmuted: {client[1]} ({ip_address})")

    if unmuted_count == 0:
        print(f"[-] No muted clients found with IP: {ip_address}")


def mute_nick(nickname):
    """Мут клиента по нику"""
    global muted_clients, muted_nicks
    muted_count = 0

    # Добавляем в список мьюченных ников
    if nickname not in muted_nicks:
        muted_nicks.append(nickname)

    for client in clients:
        if client[1] == nickname:
            if client[0] not in muted_clients:
                muted_clients.append(client[0])
                try:
                    client[0].send("[SERVER] You have been muted!".encode('utf-8'))
                except:
                    pass
                muted_count += 1
                print(f"[+] Muted: {client[1]}")

    if muted_count == 0:
        print(f"[-] No clients found with nickname: {nickname}")


def unmute_nick(nickname):
    """Размут клиента по никнейму"""
    global muted_clients, muted_nicks
    unmuted_count = 0

    # Удаляем из списка мьюченных никнеймов
    if nickname in muted_nicks:
        muted_nicks.remove(nickname)

    for client in clients:
        if client[1] == nickname:
            if client[0] in muted_clients:
                muted_clients.remove(client[0])
                try:
                    client[0].send("[SERVER] You have been unmuted!".encode('utf-8'))
                except:
                    pass
                unmuted_count += 1
                print(f"[+] Unmuted: {client[1]}")

    if unmuted_count == 0:
        print(f"[-] No muted clients found with nickname: {nickname}")


def show_banned():
    """Показывает список забаненных IP и никнеймов"""
    if not banned_ips and not banned_nicks:
        print("No banned IPs or nicknames")
    else:
        if banned_ips:
            print("Banned IPs:")
            for ip in banned_ips:
                print(f"  {ip}")
        if banned_nicks:
            print("Banned nicknames:")
            for nick in banned_nicks:
                print(f"  {nick}")


def show_muted():
    """Показывает список замьюченных никнеймов"""
    if not muted_nicks:
        print("No muted nicknames")
    else:
        print("Muted nicknames:")
        for nick in muted_nicks:
            print(f"  {nick}")


def show_commands():
    """Показывает список доступных команд"""
    print("\nAvailable commands:")
    print("  list - show connected clients")
    print("  banip <ip> - ban client by IP")
    print("  unbanip <ip> - unban client by IP")
    print("  bannick <nickname> - ban client by nickname")
    print("  unbannick <nickname> - unban client by nickname")
    print("  muteip <ip> - mute client by IP")
    print("  unmuteip <ip> - unmute client by IP")
    print("  mutenick <nickname> - mute client by nickname")
    print("  unmutenick <nickname> - unmute client by nickname")
    print("  banned - show banned IPs and nicknames")
    print("  muted - show muted nicknames")
    print("  commands - show this help")
    print("  quit - stop server")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    server.bind((host, port))
    server.listen(5)
    print(f" Server started on {host}:{port}")
    print("  Waiting for connections...")
    print("  Server is running in production mode")
    print("  Admin commands are disabled on Render")


    try:
        while True:
            client_socket, address = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address)
            )
            client_thread.daemon = True
            client_thread.start()
            print(f"New connection handled: {address}")

    except KeyboardInterrupt:
        print("\nServer stopped by admin")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
