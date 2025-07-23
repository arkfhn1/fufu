import os
import sys
import subprocess
import base64
import json
import datetime

VERIFY_LOG = os.path.join("client_app", "logs", "verify_log.json")

def detect_algorithm_from_bin(bin_path):
    try:
        with open(bin_path, "rb") as f:
            header = f.read(16)
        return base64.b64decode(header).decode()
    except Exception:
        return None

def log_verify(file, file_path, sig_path, key_path, status):
    os.makedirs(os.path.dirname(VERIFY_LOG), exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file": file,
        "file_path": file_path,
        "sig_path": sig_path,
        "key": os.path.basename(key_path),
        "status": status
    }

    if os.path.exists(VERIFY_LOG):
        with open(VERIFY_LOG, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)

    with open(VERIFY_LOG, "w") as f:
        json.dump(data, f, indent=2)

def verify_folder(folder_path):
    print(f"[Client] Verifying folder: {folder_path}")

    key_folder = os.path.join("client_app", "keys")
    pb_keys = [f for f in os.listdir(key_folder) if f.endswith(".bin") and "_pb_" in f]

    if not pb_keys:
        print("[✘] Tiada public key ditemui dalam client_app/keys/")
        return False, "No public key found in client_app/keys/"

    pub_key = os.path.join(key_folder, pb_keys[0])
    algo = detect_algorithm_from_bin(pub_key)
    if not algo:
        print("[✘] Gagal baca algoritma dari fail key.")
        return False, "Unable to detect algorithm from public key."

    sig_dir = os.path.join(folder_path, "signatures")
    if not os.path.exists(sig_dir):
        print("[✘] Tiada folder 'signatures/' dalam folder dipilih.")
        return False, "No 'signatures/' folder found in selected directory."

    valid = 0

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        sig_path = os.path.join(sig_dir, filename + ".sig")

        if not os.path.isfile(file_path) or not os.path.exists(sig_path):
            continue

        try:
            result = subprocess.run(
                ["./client_app/bin/verify", pub_key, file_path, sig_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"[✔] Sah: {filename}")
                log_verify(filename, file_path, sig_path, pub_key, "valid")
                valid += 1
            else:
                print(f"[✘] Tidak sah: {filename}")
                log_verify(filename, file_path, sig_path, pub_key, "invalid")
        except Exception as e:
            print(f"[!] Ralat verify {filename}: {e}")
            log_verify(filename, file_path, sig_path, pub_key, "error")

    if valid > 0:
        return True, f"{valid} file(s) verified successfully."
    else:
        return False, "No valid signatures found."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_client.py <folder_path>")
    else:
        folder = sys.argv[1]
        verify_folder(folder)
