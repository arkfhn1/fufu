import os
import tkinter as tk
from tkinter import ttk
from keygen_admin import build_keygen_tab
from sign_admin import build_sign_tab
from verify_admin import build_verify_tab

def build_main_ui():
    root = tk.Tk()
    root.title("Admin PQC Digital Signing System")
    root.geometry("600x400")
    root.configure(bg="#f4f6fa")

    style = ttk.Style()
    style.configure("TNotebook", background="#f4f6fa", padding=10)
    style.configure("TButton", font=("Segoe UI", 11), padding=6)

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both")

    # TAB 1: Keygen
    keygen_tab = tk.Frame(notebook, bg="white")
    notebook.add(keygen_tab, text="🔑 Jana Kunci")
    build_keygen_tab(keygen_tab)

    # TAB 2: Sign
    sign_tab = tk.Frame(notebook, bg="white")
    notebook.add(sign_tab, text="✍️ Tandatangan")
    build_sign_tab(sign_tab)

    # TAB 3: Verify
    verify_tab = tk.Frame(notebook, bg="white")
    notebook.add(verify_tab, text="✅ Sahkan Tandatangan")
    build_verify_tab(verify_tab)

    root.mainloop()

if __name__ == "__main__":
    build_main_ui()
