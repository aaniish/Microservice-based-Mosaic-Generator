import os
from pathlib import Path
import subprocess
import signal

def signal_handler(sig, frame):
    print("Terminating MMG processes...")
    for process in processes:
        process.terminate()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

mmg_folder = Path("MMGs")
original_dir = os.getcwd()  
processes = []

reducer_app_path = Path("reduce.py")

if reducer_app_path.exists():
    print("Running reducer...")
    reducer_process = subprocess.Popen(["python3", reducer_app_path.name])
    processes.append(reducer_process)
else:
    print("No reducer_app.py found")

for mmg in mmg_folder.iterdir():
    if mmg.is_dir():
        app_path = mmg / "app.py"
        print(f"Checking MMG: {mmg}")  
        if app_path.exists():
            print(f"Running MMG: {mmg}")  
            os.chdir(mmg)  
            process = subprocess.Popen(["python3", app_path.name])
            processes.append(process)
            os.chdir(original_dir)  
        else:
            print(f"No app.py found in {mmg}")  

signal.pause()  