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
LOG_FILE = "tools/tmp/logs/debug.log"
SETTINGS_FILE = "tools/settings.json"

connection_started = False
connected = False

# Function to log messages when debugger is enabled
def log_debug(message):
    if DEBUGGER_ENABLED:
        with open(LOG_FILE, 'a') as log_file:
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
                connected = True

                # Extract connection info
                connection_code = entry_connection.get()
                server_ip, server_port = connection_code.split(":")
                server_port = int(server_port)

                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((server_ip, server_port))

                log_debug(f"Connected to {server_ip}:{server_port}")  # Log connection info

                connection_started = False
                connected = True

                receive_thread = threading.Thread(target=receive_messages, args=(client, text_area))
                receive_thread.start()

                # Bind the Enter key to send message
                root.bind('<Return>', lambda event: send_message(client, entry_message, text_area))

                button_send.config(command=lambda: send_message(client, entry_message, text_area))

            on_connect()

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

    # Create the debug button in the top right corner (i will use this for other settings later)
    settings_button = tk.Button(root, text="Debug", command=toggle_debugger)
    settings_button.pack(anchor="ne", padx=10, pady=5)

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    tk.Label(frame, text="Enter connection code (format: IP:PORT):").pack()

    entry_connection = tk.Entry(frame, width=30)
    entry_connection.pack()

    button_connect = tk.Button(frame, text="Connect", command=on_connect_test)
    button_connect.pack(pady=5)

    text_area = tk.Text(frame, height=15, width=50, wrap=tk.WORD, state=tk.DISABLED)
    text_area.pack(pady=5)

    entry_message = tk.Entry(frame, width=40)
    entry_message.pack(side=tk.LEFT, padx=(0, 5))

    button_send = tk.Button(frame, text="Send")
    button_send.pack(side=tk.LEFT)

    root.mainloop()

# Load debugger settings at startup
DEBUGGER_ENABLED = load_debugger_setting()

# Ensure the log file path exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Start the client application
if __name__ == "__main__":
    start_client()
