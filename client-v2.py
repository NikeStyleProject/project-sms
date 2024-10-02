import tkinter as tk
from tkinter import messagebox
import json
import socket
import threading
import subprocess
import os
import sys
import time

# Define paths for account and log files
ACCOUNT_FILE = "tools/tmp/account.json"
LOG_DIR = "tools/tmp/logs/"
SETTINGS_FILE = "tools/tmp/settings.json"

connection_started = False
connected = False
log_file_path = None  # This will store the log file path dynamically

# Function to create a new log file each time debugger is started
def create_new_log_file():
    global log_file_path
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    log_file_path = os.path.join(LOG_DIR, f"debug_{timestamp}.log")
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(log_file_path, 'w') as log_file:
        log_file.write(f"Debug log started at {timestamp}\n")
        
# Function to log messages when debugger is enabled
def log_debug(message):
    global log_file_path
    if DEBUGGER_ENABLED:
        if log_file_path is None:  # Create log file if it doesn't exist
            create_new_log_file()
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        print(message)
        
# Load debugger settings from settings.json
def load_debugger_setting():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            settings = json.load(file)
            return settings.get("debugger_enabled", False)
    return False

# Save debugger settings to settings.json
def save_debugger_setting(enabled):
    settings = {"debugger_enabled": enabled}
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings, file)

# Function to toggle debugger on or off
def toggle_debugger():
    global DEBUGGER_ENABLED
    DEBUGGER_ENABLED = not DEBUGGER_ENABLED
    save_debugger_setting(DEBUGGER_ENABLED)
    status = "enabled" if DEBUGGER_ENABLED else "disabled"
    messagebox.showinfo("Debugger", f"Debugger is now {status}")

# Function to send messages from the client
def send_message(client, entry_message, text_area):
    message = entry_message.get()
    if message:
        client.send(message.encode('utf-8'))
        entry_message.delete(0, tk.END)
        text_area.config(state=tk.NORMAL)
        text_area.insert(tk.END, f"Me: {message}\n")
        text_area.yview(tk.END)
        text_area.config(state=tk.DISABLED)
        log_debug(f"Sent message: {message}")  # Log message when sent

# Function to receive messages from the server
def receive_messages(client, text_area):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message:
                text_area.config(state=tk.NORMAL)
                text_area.insert(tk.END, message + '\n')
                text_area.yview(tk.END)
                text_area.config(state=tk.DISABLED)
                log_debug(f"Received message: {message}")  # Log received message
        except Exception as e:
            log_debug(f"Error receiving message: {e}")
            client.close()
            break

# Main function to start the client
def start_client():
    global connection_started, connected

    def on_connect_test():
        if connection_started or connected:
            tk.messagebox.showinfo("Can't connect again", "Connected to the server. Type !leave to leave the server.")
        else:
            def on_connect():
                global connection_started, connected
                connection_started = True

                try:
                    # Extract connection info
                    connection_code = entry_connection.get()
                    server_ip, server_port = connection_code.split(":")
                    server_port = int(server_port)

                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((server_ip, server_port))

                    # Log the connection (but not the nickname)
                    log_debug(f"Connected to {server_ip}:{server_port}")

                    # Send the nickname as the first message (without logging or showing in text area)
                    send_nickname(client, client_username)

                    connected = True
                    receive_thread = threading.Thread(target=receive_messages, args=(client, text_area))
                    receive_thread.start()

                    # Bind the Enter key to send a message
                    root.bind('<Return>', lambda event: send_message(client, entry_message, text_area))

                    button_send.config(command=lambda: send_message(client, entry_message, text_area))

                except Exception as e:
                    tk.messagebox.showerror("Connection Error", f"Failed to connect to the server: {e}")
                    connection_started = False
                    connected = False

            on_connect()

    # Function to start the server script
    def start_server():
        server_script = os.path.join("tools", "server.py")
        if os.path.exists(server_script):
            subprocess.Popen(["python", server_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            tk.messagebox.showerror("Error", "Server script not found.")

    # Function to send the nickname (without showing in the text area or logging)
    def send_nickname(client, nickname):
        try:
            nickname_message = f"{nickname}"  # Use a command-like format for the nickname
            client.send(nickname_message.encode('utf-8'))
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to send nickname: {e}")

    # Check if account file exists before running the client
    if not os.path.exists(ACCOUNT_FILE):
        tk.messagebox.showerror("Error", "Account file not found. Create an account first.")
        sys.exit()
    else:
        with open(ACCOUNT_FILE, 'r') as file:
            accountJSON = json.load(file)
            global client_username
            client_username = accountJSON['username']

    # Start the main application UI
    root = tk.Tk()
    root.title("Project SMS")

    # Create the main frame to organize widgets
    main_frame = tk.Frame(root)
    main_frame.pack(padx=10, pady=10)

    # Create the debug button in the top-right corner
    settings_button = tk.Button(main_frame, text="Debug", command=toggle_debugger)
    settings_button.grid(row=0, column=1, sticky="e", padx=5, pady=5)

    # Create the server button in the top-left corner
    server_button = tk.Button(main_frame, text="Server", command=start_server)
    server_button.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    # Add a label and connection entry
    tk.Label(main_frame, text="Enter connection code (format: IP:PORT):").grid(row=1, column=0, columnspan=2, pady=5)

    entry_connection = tk.Entry(main_frame, width=30)
    entry_connection.grid(row=2, column=0, columnspan=2, pady=5)

    button_connect = tk.Button(main_frame, text="Connect", command=on_connect_test)
    button_connect.grid(row=3, column=0, columnspan=2, pady=5)

    # Add a text area for messages
    text_area = tk.Text(main_frame, height=15, width=50, wrap=tk.WORD, state=tk.DISABLED)
    text_area.grid(row=4, column=0, columnspan=2, pady=5)

    # Add message entry and send button
    entry_message = tk.Entry(main_frame, width=40)
    entry_message.grid(row=5, column=0, padx=5, pady=5, sticky="w")

    button_send = tk.Button(main_frame, text="Send")
    button_send.grid(row=5, column=1, padx=5, pady=5, sticky="e")

    root.mainloop()

# Load debugger settings at startup
DEBUGGER_ENABLED = load_debugger_setting()

# Start the client application
if __name__ == "__main__":
    start_client()
