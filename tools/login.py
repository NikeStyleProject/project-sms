import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import hashlib
import os
import subprocess
import sys

ACCOUNT_FILE = "account.json"
TEMP_DIR = "tmp"  # Relative to the /tools/ directory

#Encoding the password for security reasons
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_account(temp_dir):
    account_file = os.path.join(temp_dir, ACCOUNT_FILE)
    if os.path.exists(account_file):
        with open(account_file, 'r') as file:
            account_data = json.load(file)
            return account_data['username'], account_data['password']
    return None, None

def save_account(username, password, temp_dir):
    account_file = os.path.join(temp_dir, ACCOUNT_FILE)
    account_data = {'username': username, 'password': password}
    with open(account_file, 'w') as file:
        json.dump(account_data, file)

def create_account(temp_dir):
    username = simpledialog.askstring("Create Account", "Create your username:")
    password = simpledialog.askstring("Create Account", "Create your password:", show='*')
    if username and password:
        hashed_password = hash_password(password)
        save_account(username, hashed_password, temp_dir)
        messagebox.showinfo("Account Created", f"Account created successfully! Welcome, {username}.")
        return username, hashed_password
    else:
        messagebox.showwarning("Input Error", "Username and password cannot be empty.")
        return None, None

def authenticate(temp_dir):
    username, saved_password = load_account(temp_dir)
    if username and saved_password:
        password = simpledialog.askstring("Login", "Enter your password:", show='*')
        if hash_password(password) == saved_password:
            messagebox.showinfo("Login Successful", f"Welcome back, {username}!")
            return username
        else:
            messagebox.showerror("Login Failed", "Incorrect password. Exiting.")
            return None
    else:
        return create_account(temp_dir)

def main_application():
    # Run the main application
    subprocess.Popen(["python", "client-v2.py"], cwd=os.path.join(os.path.dirname(__file__), ".."))
    sys.exit()

def start_login():
    # Ensure the temporary directory exists
    temp_dir = os.path.join(os.path.dirname(__file__), TEMP_DIR)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    username = authenticate(temp_dir)
    if username:
        main_application()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    start_login()
