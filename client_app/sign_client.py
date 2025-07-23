import os
import sys
import subprocess
import base64
import json
import datetime

try:
    from tkinter import messagebox
    import tkinter as tk
    has_tk = True
except ImportError:
    has_tk = False  # Fallback for CLI-only environment

SIGN_LOG = os.path.join("client_app", "logs", "sign_log.json")

def detect_algorithm_from_bin(bin_path):
    try:
        with open(bin_path, "rb") as f:
            header = f.read(16)
        return base64.b64decode(header).decode()
    except Exception:
        return None

def log_sign(file, file_path, sig_path, key_path, status):
    os.makedirs(os.path.dirname(SIGN_LOG), exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file": file,
        "file_path": file_path,
        "sig_path": sig_path,
        "key": os.path.basename(key_path),
        "status": status
    }

    if os.path.exists(SIGN_LOG):
        with open(SIGN_LOG, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)

    with open(SIGN_LOG, "w") as f:
        json.dump(data, f, indent=2)

def custom_duplicate_prompt(filename):
    window = tk.Toplevel()
    window.title("Duplicate Signature Detected")
    window.geometry("420x160")
    window.resizable(False, False)
    window.grab_set()

    tk.Label(window, text=f"A signature for '{filename}' already exists.\nWhat would you like to do?", font=("Segoe UI", 11)).pack(pady=15)

    choice = tk.StringVar()

    def set_choice(value):
        choice.set(value)
        window.destroy()

    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="📝 Replace", width=12, command=lambda: set_choice("replace")).grid(row=0, column=0, padx=8)
    tk.Button(button_frame, text="📑 Duplicate", width=12, command=lambda: set_choice("duplicate")).grid(row=0, column=1, padx=8)
    tk.Button(button_frame, text="❌ Cancel", width=12, command=lambda: set_choice("cancel")).grid(row=0, column=2, padx=8)

    window.wait_window()
    return choice.get()

def sign_folder(folder_path, prompt_on_duplicate=True):
    print(f"[Client] Signing folder: {folder_path}")

    key_folder = os.path.join("client_app", "keys")
    pv_keys = [f for f in os.listdir(key_folder) if f.endswith(".bin") and "_pv_" in f]

    if not pv_keys:
        print("[✘] Tiada private key ditemui dalam client_app/keys/")
        return False

    priv_key = os.path.join(key_folder, pv_keys[0])
    algo = detect_algorithm_from_bin(priv_key)
    if not algo:
        print("[✘] Gagal baca algoritma dari fail key.")
        return False

    sig_dir = os.path.join(folder_path, "signatures")
    os.makedirs(sig_dir, exist_ok=True)

    success = False

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path) or filename == "signatures":
            continue

        sig_path = os.path.join(sig_dir, filename + ".sig")

        if os.path.exists(sig_path):
            if prompt_on_duplicate and has_tk:
                root = tk.Tk()
                root.withdraw()
                action = custom_duplicate_prompt(filename)
                root.destroy()

                if action == "cancel":
                    print(f"[⚠] Batal sign {filename}")
                    log_sign(filename, file_path, sig_path, priv_key, "cancelled")
                    continue
                elif action == "duplicate":
                    sig_path = os.path.join(sig_dir, filename + "_dup.sig")
                # else: replace (do nothing)
            else:
                sig_path = os.path.join(sig_dir, filename + "_dup.sig")

        try:
            result = subprocess.run(
                ["./client_app/bin/sign", priv_key, file_path, sig_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"[✔] Signed: {filename}")
                log_sign(filename, file_path, sig_path, priv_key, "success")
                success = True
            else:
                print(f"[✘] Gagal tandatangan {filename}")
                log_sign(filename, file_path, sig_path, priv_key, "failed")
        except Exception as e:
            print(f"[!] Ralat sign {filename}: {e}")
            log_sign(filename, file_path, sig_path, priv_key, "error")

    return success

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sign_client.py <folder_path>")
    else:
        folder = sys.argv[1]
        sign_folder(folder)
