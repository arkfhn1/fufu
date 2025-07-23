import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import base64
import json
import datetime

# Fungsi baca algoritma dari fail .bin
def detect_algorithm_from_bin(bin_path):
    try:
        with open(bin_path, "rb") as f:
            header = f.read(16)
        algo = base64.b64decode(header).decode()
        return algo
    except Exception:
        return None

# Lokasi fail log
SIGN_LOG_PATH = "logs/sign_log.json"

# Fungsi log aktiviti signing
def log_sign(file, file_path, sig_path, key, status):
    os.makedirs("logs", exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file": file,
        "file_path": file_path,
        "sig_path": sig_path,
        "key": os.path.basename(key),
        "status": status
    }
    try:
        if os.path.exists(SIGN_LOG_PATH):
            with open(SIGN_LOG_PATH, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(entry)

        with open(SIGN_LOG_PATH, "w") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        print(f"[!] Gagal tulis log: {e}")

# Fungsi utama untuk tandatangan fail dalam folder
def sign_files():
    folder = filedialog.askdirectory(title="Pilih Folder Fail untuk Ditandatangan")
    if not folder:
        return

    priv_key_path = filedialog.askopenfilename(title="Pilih Fail Private Key (.bin)",
                                               filetypes=[("Private Key files", "*_pv_*.bin")])
    if not priv_key_path:
        return

    algo = detect_algorithm_from_bin(priv_key_path)
    if not algo:
        messagebox.showerror("Ralat", "Gagal baca algoritma dari fail .bin")
        return

    signatures_dir = os.path.join(folder, "signatures")
    os.makedirs(signatures_dir, exist_ok=True)

    signed, skipped, failed = 0, 0, 0

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)

        if not os.path.isfile(file_path) or filename == "signatures":
            continue

        sig_path = os.path.join(signatures_dir, filename + ".sig")

        if os.path.exists(sig_path):
            pilihan = messagebox.askyesnocancel(
                "Fail .sig Telah Wujud",
                f"{filename}.sig telah wujud.\n\n"
                "Apakah tindakan anda?\n\n"
                "Yes = Duplicate (.sig baru)\n"
                "No = Skip fail ini\n"
                "Cancel = Henti semua proses",
                icon="warning"
            )

            if pilihan is None:  # Cancel
                break
            elif pilihan is False:  # No (Skip)
                skipped += 1
                log_sign(filename, file_path, sig_path, priv_key_path, "skipped")
                continue
            elif pilihan is True:  # Yes (Duplicate)
                sig_path = os.path.join(signatures_dir, filename + "_dup.sig")

        try:
            result = subprocess.run(
                ["./bin/sign_single", priv_key_path, file_path, sig_path],
                capture_output=True,
                text=True,
                cwd="admin_app"
            )

            if result.returncode == 0:
                signed += 1
                log_sign(filename, file_path, sig_path, priv_key_path, "success")
            else:
                failed += 1
                log_sign(filename, file_path, sig_path, priv_key_path, "failed")
                messagebox.showerror(
                    "Gagal Tandatangan",
                    f"Gagal sign {filename}\n\n{result.stderr}"
                )

        except Exception as e:
            failed += 1
            messagebox.showerror("Ralat", f"Gagal proses tandatangan:\n{e}")

    messagebox.showinfo(
        "Selesai",
        f"✔ Berjaya tandatangan: {signed}\n"
        f"↩ Skip: {skipped}\n"
        f"✘ Gagal: {failed}"
    )

def build_sign_tab(parent):
    frame = tk.Frame(parent, bg="white")
    frame.pack(expand=True, fill="both")

    label = tk.Label(frame, text="Tandatangan Fail dalam Folder", font=("Segoe UI", 14), bg="white")
    label.pack(pady=30)

    sign_btn = ttk.Button(frame, text="Pilih Folder untuk Tandatangan", command=sign_files)
    sign_btn.pack(pady=10)


# UI utama
def main():
    root = tk.Tk()
    root.title("Alat Sign Admin")
    root.geometry("400x200")

    ttk.Style().configure("TButton", font=("Segoe UI", 12), padding=10)

    label = tk.Label(root, text="PQC Digital Signature - Admin", font=("Segoe UI", 14))
    label.pack(pady=20)

    sign_btn = ttk.Button(root, text="Pilih Folder untuk Tandatangan Fail", command=sign_files)
    sign_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
