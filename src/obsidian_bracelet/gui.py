from __future__ import annotations
from pathlib import Path
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from .planner import build_plan
from .apply import apply_plan

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

def _format_actions_by_type(plan: dict):
    all_rows = []
    for i, a in enumerate(plan.get("actions", []), start=1):
        t = a.get("type")
        if t in ("copy", "rename_copy"):
            row = (i, t, a.get("src", ""), a.get("dest", ""))
        elif t == "merge_markdown":
            row = (i, t, a.get("src_a", ""), a.get("src_b", ""))
        elif t == "merge_settings":
            row = (i, t, ",".join(a.get("sources", [])), a.get("dest", ""))
        elif t == "mkdir":
            row = (i, t, a.get("path", "."), "")
        else:
            row = (i, t or "", "", "")
        all_rows.append(row)
    return all_rows

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Obsidian Bracelet - Vault Merger")
        self.geometry("800x700")

        self.sources = []

        # Title
        self.title_label = ctk.CTkLabel(self, text="Obsidian Bracelet", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=10)

        # Source vaults
        self.source_frame = ctk.CTkFrame(self)
        self.source_frame.pack(pady=10, padx=20, fill="x")

        self.source_label = ctk.CTkLabel(self.source_frame, text="Source Vaults:", font=ctk.CTkFont(weight="bold"))
        self.source_label.pack(anchor="w", padx=10, pady=(10,5))

        self.source_listbox = tk.Listbox(self.source_frame, height=4, font=("Arial", 10))
        self.source_listbox.pack(fill="x", padx=10, pady=(0,10))

        self.source_buttons_frame = ctk.CTkFrame(self.source_frame, fg_color="transparent")
        self.source_buttons_frame.pack(fill="x", padx=10, pady=(0,10))

        self.add_source_btn = ctk.CTkButton(self.source_buttons_frame, text="Add Source Folder", command=self.add_source)
        self.add_source_btn.pack(side="left", padx=(0,10))

        self.remove_source_btn = ctk.CTkButton(self.source_buttons_frame, text="Remove Selected", command=self.remove_source, fg_color="red")
        self.remove_source_btn.pack(side="left")

        # Target vault
        self.target_frame = ctk.CTkFrame(self)
        self.target_frame.pack(pady=10, padx=20, fill="x")

        self.target_label = ctk.CTkLabel(self.target_frame, text="Target Vault:", font=ctk.CTkFont(weight="bold"))
        self.target_label.pack(anchor="w", padx=10, pady=(10,5))

        self.target_entry = ctk.CTkEntry(self.target_frame, placeholder_text="Select target folder")
        self.target_entry.pack(side="left", fill="x", expand=True, padx=(10,5), pady=(0,10))

        self.browse_target_btn = ctk.CTkButton(self.target_frame, text="Browse", command=self.browse_target)
        self.browse_target_btn.pack(side="right", padx=(0,10), pady=(0,10))

        # Build button
        self.build_btn = ctk.CTkButton(self, text="Build Plan", command=self.build_plan, fg_color="green", font=ctk.CTkFont(size=14, weight="bold"))
        self.build_btn.pack(pady=10)

        # Status
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12, slant="italic"))
        self.status_label.pack(pady=5)

        # Table
        self.table_label = ctk.CTkLabel(self, text="Plan Actions:", font=ctk.CTkFont(weight="bold"))
        self.table_label.pack(anchor="w", padx=20, pady=(10,5))
        self.table_label.pack_forget()

        self.tree = ttk.Treeview(self, columns=("ID", "Type", "Src/SrcA", "Dest/SrcB"), show="headings", height=8)
        self.tree.heading("ID", text="#")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Src/SrcA", text="Src/SrcA")
        self.tree.heading("Dest/SrcB", text="Dest/SrcB")
        self.tree.column("ID", width=50)
        self.tree.column("Type", width=100)
        self.tree.column("Src/SrcA", width=200)
        self.tree.column("Dest/SrcB", width=200)
        self.tree.pack(pady=5, padx=20, fill="x")
        self.tree.pack_forget()

        # Apply section
        self.apply_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.apply_frame.pack(pady=10, padx=20, fill="x")

        self.dry_run_checkbox = ctk.CTkCheckBox(self.apply_frame, text="Dry run")
        self.dry_run_checkbox.pack(side="left", padx=(0,20))

        self.apply_btn = ctk.CTkButton(self.apply_frame, text="Apply Plan", command=self.apply_plan, fg_color="orange", font=ctk.CTkFont(size=14, weight="bold"))
        self.apply_btn.pack(side="right")

        self.apply_frame.pack_forget()

        # Notes
        self.notes_label = ctk.CTkLabel(self, text="Notes & Warnings:", font=ctk.CTkFont(weight="bold"))
        self.notes_label.pack(anchor="w", padx=20, pady=(10,5))
        self.notes_label.pack_forget()

        self.notes_textbox = ctk.CTkTextbox(self, wrap="word", height=100)
        self.notes_textbox.pack(pady=5, padx=20, fill="x")
        self.notes_textbox.pack_forget()

        self.plan = None

    def add_source(self):
        folder = filedialog.askdirectory(title="Select Source Vault Folder")
        if folder:
            self.sources.append(Path(folder))
            self.update_source_list()

    def remove_source(self):
        selection = self.source_listbox.curselection()
        if selection:
            index = selection[0]
            del self.sources[index]
            self.update_source_list()

    def update_source_list(self):
        self.source_listbox.delete(0, tk.END)
        for src in self.sources:
            self.source_listbox.insert(tk.END, str(src))

    def browse_target(self):
        folder = filedialog.askdirectory(title="Select Target Vault Folder")
        if folder:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, folder)

    def build_plan(self):
        target_text = self.target_entry.get()
        if not self.sources:
            self.status_label.configure(text="Please add at least one source vault.", text_color="red")
            return
        if not target_text:
            self.status_label.configure(text="Please select a target vault path.", text_color="red")
            return
        target = Path(target_text)
        try:
            self.plan = build_plan(self.sources, target)
            all_rows = _format_actions_by_type(self.plan)
            self.tree.delete(*self.tree.get_children())
            for row in all_rows:
                self.tree.insert("", tk.END, values=row)
            self.table_label.pack(anchor="w", padx=20, pady=(10,5))
            self.tree.pack(pady=5, padx=20, fill="x")
            self.apply_frame.pack(pady=10, padx=20, fill="x")
            notes = json.dumps({"notes": self.plan.get("notes", []), "warnings": self.plan.get("warnings", [])}, indent=2)
            self.notes_textbox.delete("0.0", tk.END)
            self.notes_textbox.insert("0.0", notes)
            self.notes_label.pack(anchor="w", padx=20, pady=(10,5))
            self.notes_textbox.pack(pady=5, padx=20, fill="x")
            self.status_label.configure(text="Plan built successfully", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Error building plan: {e}", text_color="red")

    def apply_plan(self):
        if self.plan:
            dry_run = self.dry_run_checkbox.get()
            try:
                apply_plan(self.plan, dry_run=dry_run)
                status = "Success" + (" (dry run)" if dry_run else "")
                self.status_label.configure(text=status, text_color="green")
            except Exception as e:
                self.status_label.configure(text=f"Error applying plan: {e}", text_color="red")

def main(source=None, target=None, plan_file=None):
    import tkinter as tk
    app = App()
    app.mainloop()
