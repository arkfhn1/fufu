import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# Senarai algoritma PQC
ALGORITHMS = [
    "Dilithium2",
    "Dilithium3",
    "Falcon512",
    "Falcon1024",
    "SPHINCS+-SHA256-128f-robust"
]

def detect_app_name():
    script_path = os.path.abspath(__file__)
    app_root = os.path.dirname(os.path.dirname(script_path))
    return os.path.basename(app_root)

def generate_keypair():
    app_name = detect_app_name()
    company = entry_company.get().strip()
    tujuan = entry_tujuan.get().strip()
    algo = algo_var.get()

    if not company or not tujuan or not algo:
        messagebox.showerror("Ralat", "Sila lengkapkan semua maklumat.")
        return

    # Lokasi simpan key ikut syarikat
    key_folder = os.path.join("admin_app", "keys", company)
    os.makedirs(key_folder, exist_ok=True)

    pb_path = os.path.join(key_folder, f"{app_name}_pb_{tujuan}.bin")
    pv_path = os.path.join(key_folder, f"{app_name}_pv_{tujuan}.bin")

    keygen_path = os.path.join(os.path.dirname(__file__), "bin", "keygen")

    try:
        result = subprocess.run(
            [keygen_path, algo, pb_path, pv_path],
            capture_output=True,
            text=True,
            check=True
        )
        messagebox.showinfo("Berjaya", f"Kunci berjaya dijana:\n{pb_path}\n{pv_path}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Gagal", f"Ralat semasa jana kunci:\n{e.stderr}")

def build_keygen_tab(notebook):
    frame = tk.Frame(notebook, bg="#f4f6fa")
    frame.pack(fill="both", expand=True)

    title = tk.Label(frame, text="🛡️ PQC Key Generator", font=("Helvetica", 16, "bold"), bg="#f4f6fa", fg="#2f80ed")
    title.pack(pady=10)

    inner_frame = tk.Frame(frame, bg="#f4f6fa")
    inner_frame.pack(pady=10)

    global entry_company, entry_tujuan, algo_var

    tk.Label(inner_frame, text="Nama Syarikat:", bg="#f4f6fa").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    entry_company = tk.Entry(inner_frame, width=30)
    entry_company.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(inner_frame, text="Tujuan Kunci:", bg="#f4f6fa").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    entry_tujuan = tk.Entry(inner_frame, width=30)
    entry_tujuan.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(inner_frame, text="Algoritma PQC:", bg="#f4f6fa").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    algo_var = tk.StringVar()
    algo_dropdown = ttk.Combobox(inner_frame, textvariable=algo_var, values=ALGORITHMS, state="readonly", width=27)
    algo_dropdown.grid(row=2, column=1, padx=5, pady=5)
    algo_dropdown.set(ALGORITHMS[0])

    btn = tk.Button(frame, text="Generate Keypair", command=generate_keypair, bg="#2f80ed", fg="white", padx=10, pady=5)
    btn.pack(pady=20)

# Untuk jalankan sebagai aplikasi berasingan (optional)
def main():
    root = tk.Tk()
    root.title("PQC Key Generator (Admin)")
    root.geometry("500x300")
    root.configure(bg="#f4f6fa")
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    build_keygen_tab(notebook)
    root.mainloop()

if __name__ == "__main__":
    main()
