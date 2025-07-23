import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import base64
import json
import datetime

VERIFY_LOG_PATH = "logs/verify_log.json"

def detect_algorithm_from_bin(bin_path):
    try:
        with open(bin_path, "rb") as f:
            header = f.read(16)
        algo = base64.b64decode(header).decode()
        return algo
    except Exception:
        return None

def log_verify(file, file_path, sig_path, key, result):
    os.makedirs("logs", exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file": file,
        "file_path": file_path,
        "sig_path": sig_path,
        "key": os.path.basename(key),
        "result": result
    }
    try:
        if os.path.exists(VERIFY_LOG_PATH):
            with open(VERIFY_LOG_PATH, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(entry)

        with open(VERIFY_LOG_PATH, "w") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        print(f"[!] Gagal tulis log verify: {e}")

def verify_files():
    folder = filedialog.askdirectory(title="Pilih Folder Fail untuk Disahkan")
    if not folder:
        return

    pub_key_path = filedialog.askopenfilename(title="Pilih Fail Public Key (.bin)",
                                              filetypes=[("Public Key files", "*_pb_*.bin")])
    if not pub_key_path:
        return

    algo = detect_algorithm_from_bin(pub_key_path)
    if not algo:
        messagebox.showerror("Ralat", "Gagal baca algoritma dari fail .bin")
        return

    signatures_dir = os.path.join(folder, "signatures")
    if not os.path.exists(signatures_dir):
        messagebox.showerror("Ralat", "Folder signatures/ tidak wujud dalam folder terpilih.")
        return

    verified, failed = 0, 0

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        sig_path = os.path.join(signatures_dir, filename + ".sig")

        if not os.path.isfile(file_path):
            continue
        if not os.path.exists(sig_path):
            continue

        try:
            result = subprocess.run(
                ["./bin/verify_single", pub_key_path, file_path, sig_path],
                capture_output=True,
                text=True,
                cwd="admin_app"
            )

            if result.returncode == 0:
                verified += 1
                log_verify(filename, file_path, sig_path, pub_key_path, "valid")
            else:
                # Cuba fallback ke fail .sig_dup jika ada
                alt_sig = os.path.join(signatures_dir, filename + "_dup.sig")
                if os.path.exists(alt_sig):
                    result2 = subprocess.run(
                        ["./bin/verify_single", pub_key_path, file_path, alt_sig],
                        capture_output=True,
                        text=True,
                        cwd="admin_app"
                    )
                    if result2.returncode == 0:
                        verified += 1
                        log_verify(filename, file_path, alt_sig, pub_key_path, "valid (_dup)")
                        continue  # skip remaining log below

                failed += 1
                log_verify(filename, file_path, sig_path, pub_key_path, "invalid")

        except Exception as e:
            failed += 1
            log_verify(filename, file_path, sig_path, pub_key_path, "error")
            messagebox.showerror("Ralat", f"Gagal sahkan {filename}:\n{e}")

    messagebox.showinfo(
        "Selesai",
        f"✔ Tandatangan sah: {verified}\n"
        f"✘ Gagal/rosak: {failed}"
    )

def build_verify_tab(parent):
    frame = tk.Frame(parent, bg="white")
    frame.pack(expand=True, fill="both")

    label = tk.Label(frame, text="Sahkan Fail Bertandatangan", font=("Segoe UI", 14), bg="white")
    label.pack(pady=30)

    verify_btn = ttk.Button(frame, text="Pilih Folder untuk Sahkan", command=verify_files)
    verify_btn.pack(pady=10)


def main():
    root = tk.Tk()
    root.title("Alat Verify Admin")
    root.geometry("400x200")

    ttk.Style().configure("TButton", font=("Segoe UI", 12), padding=10)

    label = tk.Label(root, text="PQC Digital Signature - Admin (Verify)", font=("Segoe UI", 14))
    label.pack(pady=20)

    verify_btn = ttk.Button(root, text="Pilih Folder untuk Sahkan Fail", command=verify_files)
    verify_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
