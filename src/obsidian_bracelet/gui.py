from __future__ import annotations
from pathlib import Path
import json
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .planner import build_plan
from .apply import apply_plan

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

def _format_actions_by_type(plan: dict):
    # Sort actions by type first, then by original order
    actions = plan.get("actions", [])
    action_type_order = ["mkdir", "copy", "rename_copy", "merge_markdown", "create_link_file", "update_file_links", "merge_settings"]
    
    # Group actions by type
    grouped_actions = {}
    for action in actions:
        action_type = action.get("type")
        if action_type not in grouped_actions:
            grouped_actions[action_type] = []
        grouped_actions[action_type].append(action)
    
    # Sort groups by predefined order, then alphabetically for unknown types
    sorted_groups = []
    for action_type in action_type_order:
        if action_type in grouped_actions:
            sorted_groups.append((action_type, grouped_actions[action_type]))
    
    # Add any remaining action types
    for action_type in sorted(grouped_actions.keys()):
        if action_type not in action_type_order:
            sorted_groups.append((action_type, grouped_actions[action_type]))
    
    # Create rows
    all_rows = []
    counter = 1
    for action_type, action_list in sorted_groups:
        for a in action_list:
            t = a.get("type")
            if t in ("copy", "rename_copy"):
                row = (counter, t, a.get("src", ""), a.get("dest", ""))
            elif t == "merge_markdown":
                row = (counter, t, a.get("src_a", ""), a.get("src_b", ""))
            elif t == "merge_settings":
                row = (counter, t, ",".join(a.get("sources", [])), a.get("dest", ""))
            elif t == "mkdir":
                row = (counter, t, a.get("path", "."), "")
            elif t == "create_link_file":
                row = (counter, t, "", a.get("link_to", ""))
            elif t == "update_file_links":
                row = (counter, t, a.get("file", ""), f"Updates: {len(a.get('link_updates', {}))} links")
            else:
                row = (counter, t or "", "", "")
            all_rows.append(row)
            counter += 1
    return all_rows

def _create_plan_summary(plan: dict):
    """Create a summary of planned operations by type"""
    actions = plan.get("actions", [])
    excluded_files = plan.get("excluded_files", [])
    
    # Count actions by type
    action_counts = {}
    for action in actions:
        action_type = action.get("type")
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
    
    # Create summary text
    summary_parts = []
    
    # Add action counts
    type_descriptions = {
        "copy": "📁 Copy",
        "rename_copy": "📝 Rename Copy",
        "merge_markdown": "🔀 Merge",
        "create_link_file": "🔗 Link",
        "update_file_links": "🔄 Link Updates",
        "merge_settings": "⚙️ Settings",
        "mkdir": "📂 Create Dir"
    }
    
    for action_type, count in sorted(action_counts.items()):
        description = type_descriptions.get(action_type, action_type)
        summary_parts.append(f"{count}× {description}")
    
    # Add excluded files count
    if excluded_files:
        summary_parts.append(f"🚫 {len(excluded_files)}× Excluded")
    
    return " | ".join(summary_parts) if summary_parts else "No operations planned"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Obsidian Bracelet - Vault Merger")
        self.geometry("1000x800")

        self.sources = []

        # Create a scrollable frame for the entire content
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        self.title_label = ctk.CTkLabel(self.scrollable_frame, text="Obsidian Bracelet", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=10)

        # Source and Target vaults in two columns
        self.vaults_frame = ctk.CTkFrame(self.scrollable_frame)
        self.vaults_frame.pack(pady=10, padx=20, fill="x")

        # Left column - Source vaults
        self.source_frame = ctk.CTkFrame(self.vaults_frame)
        self.source_frame.pack(side="left", fill="both", expand=True, padx=(10,5), pady=10)

        self.source_label = ctk.CTkLabel(self.source_frame, text="Source Vaults:", font=ctk.CTkFont(weight="bold"))
        self.source_label.pack(anchor="w", padx=10, pady=(10,5))

        self.source_listbox = tk.Listbox(self.source_frame, height=4, font=("Arial", 10))
        self.source_listbox.pack(fill="both", expand=True, padx=10, pady=(0,5))

        self.source_buttons_frame = ctk.CTkFrame(self.source_frame, fg_color="transparent")
        self.source_buttons_frame.pack(fill="x", padx=10, pady=(0,10))

        self.add_source_btn = ctk.CTkButton(self.source_buttons_frame, text="Add Source", command=self.add_source)
        self.add_source_btn.pack(side="left", padx=(0,5))

        self.remove_source_btn = ctk.CTkButton(self.source_buttons_frame, text="Remove", command=self.remove_source, fg_color="red")
        self.remove_source_btn.pack(side="left")

        # Right column - Target vault
        self.target_frame = ctk.CTkFrame(self.vaults_frame)
        self.target_frame.pack(side="right", fill="both", expand=True, padx=(5,10), pady=10)

        self.target_label = ctk.CTkLabel(self.target_frame, text="Target Vault:", font=ctk.CTkFont(weight="bold"))
        self.target_label.pack(anchor="w", padx=10, pady=(10,5))

        self.target_entry = ctk.CTkEntry(self.target_frame, placeholder_text="Select target folder")
        self.target_entry.pack(fill="x", padx=10, pady=(0,5))

        self.browse_target_btn = ctk.CTkButton(self.target_frame, text="Browse Target", command=self.browse_target)
        self.browse_target_btn.pack(pady=(0,10))

        # Ignore patterns
        self.ignore_frame = ctk.CTkFrame(self.scrollable_frame)
        self.ignore_frame.pack(pady=10, padx=20, fill="x")

        self.ignore_label = ctk.CTkLabel(self.ignore_frame, text="Ignore Patterns (regex, comma-separated):", font=ctk.CTkFont(weight="bold"))
        self.ignore_label.pack(anchor="w", padx=10, pady=(10,5))

        self.ignore_entry = ctk.CTkEntry(self.ignore_frame, placeholder_text="e.g., \\.tmp$, backup/.*")
        self.ignore_entry.pack(fill="x", padx=10, pady=(0,10))

        # Build button
        self.build_btn = ctk.CTkButton(self.scrollable_frame, text="Build Plan", command=self.build_plan, fg_color="green", font=ctk.CTkFont(size=14, weight="bold"))
        self.build_btn.pack(pady=10)

        # Status
        self.status_label = ctk.CTkLabel(self.scrollable_frame, text="", font=ctk.CTkFont(size=12, slant="italic"))
        self.status_label.pack(pady=5)

        # Verbose logging field - moved to be right after Build Plan button
        self.logging_label = ctk.CTkLabel(self.scrollable_frame, text="Planning Log:", font=ctk.CTkFont(weight="bold"))
        self.logging_label.pack(anchor="w", padx=20, pady=(10,5))
        self.logging_label.pack_forget()

        self.logging_textbox = ctk.CTkTextbox(self.scrollable_frame, wrap="word", height=150)
        self.logging_textbox.pack(pady=5, padx=20, fill="both", expand=True)
        self.logging_textbox.pack_forget()

        # Plan Summary
        self.summary_frame = ctk.CTkFrame(self.scrollable_frame)
        self.summary_frame.pack(pady=10, padx=20, fill="x")
        self.summary_frame.pack_forget()

        self.summary_label = ctk.CTkLabel(self.summary_frame, text="Plan Summary:", font=ctk.CTkFont(weight="bold"))
        self.summary_label.pack(anchor="w", padx=10, pady=(10,5))

        self.summary_text = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=12))
        self.summary_text.pack(anchor="w", padx=10, pady=(0,10))

        # Table
        self.table_label = ctk.CTkLabel(self.scrollable_frame, text="Plan Actions:", font=ctk.CTkFont(weight="bold"))
        self.table_label.pack(anchor="w", padx=20, pady=(10,5))
        self.table_label.pack_forget()

        # Create a scrollable frame for the tree view
        self.tree_frame = ctk.CTkScrollableFrame(self.scrollable_frame, height=300)
        self.tree_frame.pack(pady=5, padx=20, fill="both", expand=True)
        self.tree_frame.pack_forget()

        self.tree = ttk.Treeview(self.tree_frame, columns=("ID", "Type", "Src/SrcA", "Dest/SrcB"), show="headings")
        self.tree.heading("ID", text="#")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Src/SrcA", text="Src/SrcA")
        self.tree.heading("Dest/SrcB", text="Dest/SrcB")
        self.tree.column("ID", width=50)
        self.tree.column("Type", width=120)
        self.tree.column("Src/SrcA", width=250)
        self.tree.column("Dest/SrcB", width=250)
        self.tree.pack(fill="both", expand=True)

        # Apply section
        self.apply_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.apply_frame.pack(pady=10, padx=20, fill="x")

        self.dry_run_checkbox = ctk.CTkCheckBox(self.apply_frame, text="Dry run")
        self.dry_run_checkbox.pack(side="left", padx=(0,20))

        self.apply_btn = ctk.CTkButton(self.apply_frame, text="Apply Plan", command=self.apply_plan, fg_color="orange", font=ctk.CTkFont(size=14, weight="bold"))
        self.apply_btn.pack(side="right")

        self.apply_frame.pack_forget()

        # Notes
        self.notes_label = ctk.CTkLabel(self.scrollable_frame, text="Notes & Warnings:", font=ctk.CTkFont(weight="bold"))
        self.notes_label.pack(anchor="w", padx=20, pady=(10,5))
        self.notes_label.pack_forget()

        self.notes_textbox = ctk.CTkTextbox(self.scrollable_frame, wrap="word", height=100)
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
        ignore_text = self.ignore_entry.get()
        ignore_patterns = [p.strip() for p in ignore_text.split(',') if p.strip()]
        
        # Capture verbose output
        verbose_output = []
        
        try:
            self.plan = build_plan(self.sources, target, ignore_patterns=ignore_patterns, verbose_output=verbose_output)
            all_rows = _format_actions_by_type(self.plan)
            
            # Update summary
            summary = _create_plan_summary(self.plan)
            self.summary_text.configure(text=summary)
            
            # Update table
            self.tree.delete(*self.tree.get_children())
            for row in all_rows:
                self.tree.insert("", tk.END, values=row)
            
            # Update verbose logging field first and show it immediately
            self.logging_textbox.delete("0.0", tk.END)
            if verbose_output:
                self.logging_textbox.insert("0.0", "\n".join(verbose_output))
            self.logging_label.pack(anchor="w", padx=20, pady=(10,5))
            self.logging_textbox.pack(pady=5, padx=20, fill="both", expand=True)
            
            # Show all plan-related elements
            self.summary_frame.pack(pady=10, padx=20, fill="x")
            self.table_label.pack(anchor="w", padx=20, pady=(10,5))
            self.tree_frame.pack(pady=5, padx=20, fill="both", expand=True)
            self.apply_frame.pack(pady=10, padx=20, fill="x")
            
            # Update notes
            notes = json.dumps({"notes": self.plan.get("notes", []), "warnings": self.plan.get("warnings", []), "excluded_files": self.plan.get("excluded_files", [])}, indent=2)
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

def build_plan_action(sources_str: str, target_str: str) -> tuple:
    sources = [Path(s.strip()) for s in sources_str.split('\n') if s.strip()]
    target = Path(target_str)
    if not sources or not target_str:
        return "", [], {}, "Please provide at least one source vault and a target path.", [], [], [], []
    try:
        verbose_output = []
        plan = build_plan(sources, target, verbose_output=verbose_output)
        all_rows = _format_actions_by_type(plan)
        copy_table = [r for r in all_rows if r[1] == "copy"]
        md_table = [r for r in all_rows if r[1] == "merge_markdown"]
        rename_table = [r for r in all_rows if r[1] == "rename_copy"]
        settings_table = [r for r in all_rows if r[1] == "merge_settings"]
        plan_json = json.dumps(plan, indent=2)
        details = json.dumps({"notes": plan.get("notes", []), "warnings": plan.get("warnings", []), "excluded_files": plan.get("excluded_files", [])}, indent=2)
        verbose_log = "\n".join(verbose_output)
        return plan_json, all_rows, details, "", md_table, rename_table, settings_table, copy_table, verbose_log
    except Exception as e:
        return "", [], {}, str(e), [], [], [], [], ""


def main(source=None, target=None, plan_file=None):
    app = App()
    app.mainloop()
