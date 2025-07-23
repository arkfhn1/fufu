import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess

LOG_SIGN = "client_app/logs/sign_log.json"
LOG_VERIFY = "client_app/logs/verify_log.json"

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Client Digital Signature")
        self.root.geometry("600x400")
        self.root.configure(bg="#f4f6fa")

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 11))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.build_sign_tab()
        self.build_verify_tab()
        self.build_log_tab()

    def build_sign_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="✍️ Tandatangan")

        lbl = tk.Label(tab, text="Pilih folder untuk tandatangan:", font=("Segoe UI", 12), bg="white")
        lbl.pack(pady=20)

        btn = ttk.Button(tab, text="Sign Folder", command=self.sign_folder)
        btn.pack()

    def build_verify_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="✅ Sahkan")

        lbl = tk.Label(tab, text="Pilih folder untuk disahkan:", font=("Segoe UI", 12), bg="white")
        lbl.pack(pady=20)

        btn = ttk.Button(tab, text="Verify Folder", command=self.verify_folder)
        btn.pack()

    def build_log_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📜 Log Aktiviti")

        self.log_text = tk.Text(tab, wrap="word", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        btn = ttk.Button(tab, text="Refresh Log", command=self.load_logs)
        btn.pack(pady=5)

    def load_logs(self):
        logs = []
        for log_file in [LOG_SIGN, LOG_VERIFY]:
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    data = json.load(f)
                    logs.extend(data)

        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        self.log_text.delete("1.0", tk.END)
        for entry in logs:
            self.log_text.insert(tk.END, json.dumps(entry, indent=2) + "\n\n")

    def sign_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder untuk Tandatangan")
        if not folder:
            return

        try:
            subprocess.run(["python3", "client_app/sign_client.py", folder], check=True)
            messagebox.showinfo("Berjaya", "Tandatangan selesai.")
        except subprocess.CalledProcessError:
            messagebox.showerror("Ralat", "Tandatangan gagal.")

    def verify_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder untuk Sahkan")
        if not folder:
            return

        try:
            subprocess.run(["python3", "client_app/verify_client.py", folder], check=True)
            messagebox.showinfo("Berjaya", "Sahkan tandatangan selesai.")
        except subprocess.CalledProcessError:
            messagebox.showerror("Ralat", "Sahkan tandatangan gagal.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
