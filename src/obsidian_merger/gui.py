from __future__ import annotations
import json
from pathlib import Path
import PySimpleGUI as sg

def _load_or_build_plan(source, target, plan_file):
    if plan_file:
        return json.loads(Path(plan_file).read_text())
    from .planner import build_plan
    sources = [Path(p).resolve() for p in (source or [])]
    tgt = Path(target).resolve()
    return build_plan(sources, tgt)

def main(source=None, target=None, plan_file=None):
    sg.theme("SystemDefault")
    plan = None
    try:
        plan = _load_or_build_plan(source, target, plan_file)
    except Exception as e:
        sg.popup_error(f"Failed to load/build plan: {e}")
        return

    actions = plan.get("actions", [])
    headings = ["#", "type", "src/src_a", "dest/src_b"]
    data = []
    for i, a in enumerate(actions, 1):
        if a["type"] in ("copy", "rename_copy"):
            data.append([i, a["type"], a.get("src", ""), a.get("dest", "")])
        elif a["type"] == "merge_markdown":
            data.append([i, a["type"], a.get("src_a", ""), a.get("src_b", "")])
        elif a["type"] == "merge_settings":
            data.append([i, a["type"], ",".join(a.get("sources", [])), a.get("dest", "")])
        else:
            data.append([i, a["type"], "", ""])

    layout = [
        [sg.Text("Review planned actions before applying")],
        [sg.Table(values=data, headings=headings, key="-TABLE-", auto_size_columns=True, expand_x=True, expand_y=True, enable_events=True)],
        [sg.Multiline(key="-DETAILS-", size=(100, 8), disabled=True, autoscroll=True, expand_x=True)],
        [sg.Checkbox("Dry run", key="-DRY-", default=False), sg.Push(), sg.Button("Apply"), sg.Button("Close")],
    ]
    win = sg.Window("Obsidian Vault Merger", layout, resizable=True, finalize=True)

    while True:
        ev, vals = win.read()
        if ev in (sg.WINDOW_CLOSED, "Close"):
            break
        if ev == "-TABLE-":
            sel = vals["-TABLE-"]
            if sel:
                idx = sel[0]
                a = actions[idx]
                win["-DETAILS-"].update(json.dumps(a, indent=2))
        if ev == "Apply":
            from .apply import apply_plan
            try:
                apply_plan(plan, dry_run=bool(vals["-DRY-"]))
                sg.popup_ok("Apply completed successfully")
            except Exception as e:
                sg.popup_error(f"Apply failed: {e}")

    win.close()
