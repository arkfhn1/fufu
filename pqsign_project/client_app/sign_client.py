import os
import sys
import subprocess
import base64
import json
import datetime

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

def sign_folder(folder_path):
    print(f"[Client] Signing folder: {folder_path}")

    # Cari private key dalam client_app/keys
    key_folder = os.path.join("client_app", "keys")
    pv_keys = [f for f in os.listdir(key_folder) if f.endswith(".bin") and "_pv_" in f]

    if not pv_keys:
        print("[✘] Tiada private key ditemui dalam client_app/keys/")
        return

    priv_key = os.path.join(key_folder, pv_keys[0])
    algo = detect_algorithm_from_bin(priv_key)
    if not algo:
        print("[✘] Gagal baca algoritma dari fail key.")
        return

    sig_dir = os.path.join(folder_path, "signatures")
    os.makedirs(sig_dir, exist_ok=True)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path):
            continue
        if filename == "signatures":
            continue

        sig_path = os.path.join(sig_dir, filename + ".sig")

        if os.path.exists(sig_path):
            sig_path = os.path.join(sig_dir, filename + "_dup.sig")

        try:
            result = subprocess.run(
                ["./admin_app/bin/sign", priv_key, file_path, sig_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"[✔] Signed: {filename}")
                log_sign(filename, file_path, sig_path, priv_key, "success")
            else:
                print(f"[✘] Gagal tandatangan {filename}")
                log_sign(filename, file_path, sig_path, priv_key, "failed")
        except Exception as e:
            print(f"[!] Ralat sign {filename}: {e}")
            log_sign(filename, file_path, sig_path, priv_key, "error")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sign_client.py <folder_path>")
    else:
        folder = sys.argv[1]
        sign_folder(folder)
