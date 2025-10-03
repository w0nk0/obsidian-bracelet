from __future__ import annotations
from pathlib import Path
import json

from .planner import build_plan
from .apply import apply_plan

def _path_list_from_text(text: str) -> list[Path]:
    parts = [p.strip() for p in (text or "").replace(",", "\n").splitlines() if p.strip()]
    return [Path(p).expanduser().resolve() for p in parts]

def _format_actions_by_type(plan: dict):
    # Returns dict of action_type -> list of table rows and a combined table
    groups: dict[str, list[list]] = {"merge_markdown": [], "rename_copy": [], "merge_settings": [], "mkdir": [], "copy": []}
    all_rows: list[list] = []
    for i, a in enumerate(plan.get("actions", []), start=1):
        t = a.get("type")
        if t in ("copy", "rename_copy"):
            row = [i, t, a.get("src", ""), a.get("dest", "")]
        elif t == "merge_markdown":
            row = [i, t, a.get("src_a", ""), a.get("src_b", "")]
        elif t == "merge_settings":
            row = [i, t, ",".join(a.get("sources", [])), a.get("dest", "")]
        elif t == "mkdir":
            row = [i, t, a.get("path", "."), ""]
        else:
            row = [i, t or "", "", ""]
        groups.setdefault(t, []).append(row)
        all_rows.append(row)
    return groups, all_rows

def build_plan_action(sources_text: str, target_text: str):
    sources = _path_list_from_text(sources_text)
    if not sources:
        return None, None, None, "Please provide at least one source vault path.", None, None, None, None
    if not target_text:
        return None, None, None, "Please provide a target vault path.", None, None, None, None
    target = Path(target_text).expanduser().resolve()
    plan = build_plan(sources, target)
    groups, all_rows = _format_actions_by_type(plan)
    plan_json = json.dumps(plan, indent=2, ensure_ascii=False)
    notes = json.dumps({"notes": plan.get("notes", []), "warnings": plan.get("warnings", [])}, indent=2, ensure_ascii=False)
    # Return overall table and per-group tables
    return (
        plan_json,
        all_rows,
        notes,
        "",
        groups.get("merge_markdown", []),
        groups.get("rename_copy", []),
        groups.get("merge_settings", []),
        groups.get("copy", []),
    )

def apply_action(plan_json: str, dry_run: bool):
    try:
        plan = json.loads(plan_json)
        apply_plan(plan, dry_run=dry_run)
        return "Success"
    except Exception as e:
        return f"Error: {e}"

def build_ui():
    import gradio as gr
    with gr.Blocks(title="Obsidian Vault Merger") as demo:
        gr.Markdown("# Obsidian Vault Merger")
        with gr.Row():
            sources_text = gr.Textbox(label="Source vault paths (newline or comma-separated)", lines=4)
            target_text = gr.Textbox(label="Target vault path")
        build_btn = gr.Button("Build Plan", variant="primary")
        with gr.Row():
            dry_run = gr.Checkbox(label="Dry run", value=False)
            apply_btn = gr.Button("Apply", variant="secondary")
            status = gr.Textbox(label="Status", interactive=False)
        plan_json = gr.Code(label="Plan JSON", language="json")
        details = gr.Code(label="Notes & Warnings", language="json")
        all_table = gr.Dataframe(headers=["#", "type", "src/src_a", "dest/src_b"], datatype=["number","str","str","str"], row_count=(0, "dynamic"), col_count=4, wrap=True, interactive=False)

        # Focus areas: show non-trivial actions expanded, trivial copies collapsed by default
        with gr.Accordion("Markdown merges (merge_markdown)", open=True):
            md_table = gr.Dataframe(headers=["#", "type", "src_a", "src_b"], datatype=["number","str","str","str"], row_count=(0, "dynamic"), col_count=4, wrap=True, interactive=False)
        with gr.Accordion("Renamed copies due to collisions (rename_copy)", open=True):
            rename_table = gr.Dataframe(headers=["#", "type", "src", "dest"], datatype=["number","str","str","str"], row_count=(0, "dynamic"), col_count=4, wrap=True, interactive=False)
        with gr.Accordion("Settings merge (.obsidian)", open=True):
            settings_table = gr.Dataframe(headers=["#", "type", "sources", "dest"], datatype=["number","str","str","str"], row_count=(0, "dynamic"), col_count=4, wrap=True, interactive=False)
        with gr.Accordion("Trivial copies (copy)", open=False):
            copy_table = gr.Dataframe(headers=["#", "type", "src", "dest"], datatype=["number","str","str","str"], row_count=(0, "dynamic"), col_count=4, wrap=True, interactive=False)

        build_btn.click(
            fn=build_plan_action,
            inputs=[sources_text, target_text],
            outputs=[plan_json, all_table, details, status, md_table, rename_table, settings_table, copy_table]
        )
        apply_btn.click(fn=apply_action, inputs=[plan_json, dry_run], outputs=status)
    return demo

def main(source=None, target=None, plan_file=None):
    # For simplicity, the parameters are not wired into the initial UI; user can paste values.
    demo = build_ui()
    demo.launch()
