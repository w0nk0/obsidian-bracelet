from __future__ import annotations
from pathlib import Path
import json
import PySimpleGUI as sg

from .planner import build_plan
from .apply import apply_plan

def _format_actions_by_type(plan: dict):
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
        all_rows.append(row)
    return all_rows

def main(source=None, target=None, plan_file=None):
    sg.theme('LightBlue')

    layout = [
        [sg.Text('Obsidian Bracelet - Vault Merger', font=('Any', 16))],
        [sg.Text('Source Vaults:')],
        [sg.Listbox(values=[], size=(50, 4), key='-SOURCES-', enable_events=True)],
        [sg.Button('Add Source Folder', key='-ADD_SOURCE-'), sg.Button('Remove Selected', key='-REMOVE_SOURCE-')],
        [sg.Text('Target Vault:')],
        [sg.InputText(key='-TARGET-', size=(50, 1)), sg.FolderBrowse('Browse', target='-TARGET-')],
        [sg.Button('Build Plan', key='-BUILD-')],
        [sg.Text('', key='-STATUS-', size=(50, 1))],
        [sg.Table(values=[], headings=['#', 'Type', 'Src/SrcA', 'Dest/SrcB'], key='-TABLE-', size=(60, 10), visible=False)],
        [sg.Checkbox('Dry run', key='-DRY_RUN-', visible=False)],
        [sg.Button('Apply Plan', key='-APPLY-', visible=False)],
        [sg.Multiline('', key='-NOTES-', size=(60, 5), visible=False)],
    ]

    window = sg.Window('Obsidian Bracelet', layout)

    sources = []
    plan = None

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == '-ADD_SOURCE-':
            folder = sg.popup_get_folder('Select Source Vault Folder')
            if folder:
                sources.append(Path(folder))
                window['-SOURCES-'].update(values=[str(s) for s in sources])

        if event == '-REMOVE_SOURCE-':
            selected = values['-SOURCES-']
            if selected:
                for sel in selected:
                    sources = [s for s in sources if str(s) != sel]
                window['-SOURCES-'].update(values=[str(s) for s in sources])

        if event == '-BUILD-':
            target_text = values['-TARGET-']
            if not sources:
                window['-STATUS-'].update('Please add at least one source vault.')
                continue
            if not target_text:
                window['-STATUS-'].update('Please select a target vault path.')
                continue
            target = Path(target_text)
            try:
                plan = build_plan(sources, target)
                all_rows = _format_actions_by_type(plan)
                window['-TABLE-'].update(values=all_rows, visible=True)
                window['-APPLY-'].update(visible=True)
                window['-DRY_RUN-'].update(visible=True)
                notes = json.dumps({"notes": plan.get("notes", []), "warnings": plan.get("warnings", [])}, indent=2)
                window['-NOTES-'].update(notes, visible=True)
                window['-STATUS-'].update('Plan built successfully')
            except Exception as e:
                window['-STATUS-'].update(f'Error building plan: {e}')

        if event == '-APPLY-':
            if plan:
                dry_run = values['-DRY_RUN-']
                try:
                    apply_plan(plan, dry_run=dry_run)
                    status = "Success" + (" (dry run)" if dry_run else "")
                    window['-STATUS-'].update(status)
                except Exception as e:
                    window['-STATUS-'].update(f'Error applying plan: {e}')

    window.close()
