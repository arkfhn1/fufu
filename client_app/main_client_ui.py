import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from sign_client import sign_folder
from verify_client import verify_folder

LOG_SIGN = "client_app/logs/sign_log.json"
LOG_VERIFY = "client_app/logs/verify_log.json"

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Client Digital Signature")
        self.root.geometry("700x500")
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

        btn = ttk.Button(tab, text="Sign Folder", command=self.sign_folder_ui)
        btn.pack()

    def build_verify_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="✅ Sahkan")

        lbl = tk.Label(tab, text="Pilih folder untuk disahkan:", font=("Segoe UI", 12), bg="white")
        lbl.pack(pady=20)

        btn = ttk.Button(tab, text="Verify Folder", command=self.verify_folder_ui)
        btn.pack()

    def build_log_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📜 Log Aktiviti")

        top_frame = tk.Frame(tab, bg="white")
        top_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(top_frame, text="Log Type:", bg="white").pack(side="left")
        self.log_filter = ttk.Combobox(top_frame, values=["All Logs", "Sign Logs", "Verify Logs"], state="readonly")
        self.log_filter.current(0)
        self.log_filter.pack(side="left", padx=5)
        self.log_filter.bind("<<ComboboxSelected>>", lambda e: self.load_logs())

        tk.Label(top_frame, text="Search:", bg="white").pack(side="left", padx=(20, 0))
        self.search_entry = ttk.Entry(top_frame, width=20)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_keyword())

        search_btn = ttk.Button(top_frame, text="Search", command=self.search_keyword)
        search_btn.pack(side="left", padx=(0, 5))

        prev_btn = ttk.Button(top_frame, text="◀ Previous", command=self.previous_match)
        prev_btn.pack(side="left", padx=2)

        next_btn = ttk.Button(top_frame, text="Next ▶", command=self.next_match)
        next_btn.pack(side="left", padx=2)

        self.match_label = tk.Label(top_frame, text="Matches: 0", bg="white", fg="#333")
        self.match_label.pack(side="right", padx=(0, 10))

        outer_frame = tk.Frame(tab, bg="white")
        outer_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        canvas = tk.Canvas(outer_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        self.log_text = tk.Text(canvas, wrap="word", font=("Consolas", 10), bg="white", fg="#333333")
        self.log_text.tag_config("highlight", background="#ffff00")
        self.log_text.tag_config("active_match", background="#ffcc00")
        self.log_text.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Guna ID untuk ubah saiz dinamik
        self.text_window = canvas.create_window((0, 0), window=self.log_text, anchor="nw")

        def resize_text(event):
            canvas.itemconfig(self.text_window, width=event.width)
        canvas.bind("<Configure>", resize_text)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.matches = []
        self.current_match_index = 0

        self.load_logs()

    def load_logs(self):
        logs = []
        selected = self.log_filter.get()

        if selected in ["All Logs", "Sign Logs"] and os.path.exists(LOG_SIGN):
            with open(LOG_SIGN, "r") as f:
                try:
                    logs.extend(json.load(f))
                except:
                    pass
        if selected in ["All Logs", "Verify Logs"] and os.path.exists(LOG_VERIFY):
            with open(LOG_VERIFY, "r") as f:
                try:
                    logs.extend(json.load(f))
                except:
                    pass

        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        self.log_text.delete("1.0", tk.END)
        for entry in logs:
            self.log_text.insert(tk.END, json.dumps(entry, indent=2) + "\n\n")

        self.search_keyword()

    def search_keyword(self):
        keyword = self.search_entry.get()
        self.log_text.tag_remove("highlight", "1.0", tk.END)
        self.log_text.tag_remove("active_match", "1.0", tk.END)
        self.matches = []
        self.current_match_index = 0

        if not keyword:
            self.match_label.config(text="Matches: 0")
            return

        start = "1.0"
        while True:
            pos = self.log_text.search(keyword, start, stopindex=tk.END)
            if not pos:
                break
            end = f"{pos}+{len(keyword)}c"
            self.log_text.tag_add("highlight", pos, end)
            self.matches.append((pos, end))
            start = end

        total = len(self.matches)
        if total > 0:
            self.goto_match(0)
        else:
            self.match_label.config(text="Matches: 0")

    def goto_match(self, index):
        self.log_text.tag_remove("active_match", "1.0", tk.END)
        if not self.matches:
            return
        pos, end = self.matches[index]
        self.log_text.tag_add("active_match", pos, end)
        self.log_text.see(pos)
        self.log_text.mark_set(tk.INSERT, pos)
        self.match_label.config(text=f"Match {index + 1} of {len(self.matches)}")

    def next_match(self):
        if not self.matches:
            return
        self.current_match_index = (self.current_match_index + 1) % len(self.matches)
        self.goto_match(self.current_match_index)

    def previous_match(self):
        if not self.matches:
            return
        self.current_match_index = (self.current_match_index - 1) % len(self.matches)
        self.goto_match(self.current_match_index)

    def sign_folder_ui(self):
        folder = filedialog.askdirectory(title="Pilih Folder untuk Tandatangan")
        if not folder:
            return

        status = sign_folder(folder, prompt_on_duplicate=True)
        if status:
            messagebox.showinfo("Berjaya", "Tandatangan selesai.")
        else:
            messagebox.showerror("Gagal", "Tiada tandatangan berjaya dilakukan.")

    def verify_folder_ui(self):
        folder = filedialog.askdirectory(title="Pilih Folder untuk Sahkan")
        if not folder:
            return

        status, message = verify_folder(folder)
        if status:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Failed", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
