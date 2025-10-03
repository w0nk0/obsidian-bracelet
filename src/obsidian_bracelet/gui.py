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
    sg.theme('SystemDefault')

    layout = [
        [sg.Text('Obsidian Bracelet', font=('Helvetica', 20, 'bold'), justification='center', expand_x=True, background_color='#4A90E2', text_color='white', pad=(10, 10))],
        [sg.HorizontalSeparator()],
        [sg.Text('Source Vaults:', font=('Helvetica', 12, 'bold'), background_color='#F0F0F0')],
        [sg.Listbox(values=[], size=(60, 4), key='-SOURCES-', enable_events=True, font=('Helvetica', 10), background_color='white')],
        [sg.Button('Add Source Folder', key='-ADD_SOURCE-', button_color=('white', '#4A90E2'), font=('Helvetica', 10, 'bold')),
         sg.Button('Remove Selected', key='-REMOVE_SOURCE-', button_color=('white', '#E74C3C'), font=('Helvetica', 10, 'bold'))],
        [sg.HorizontalSeparator()],
        [sg.Text('Target Vault:', font=('Helvetica', 12, 'bold'), background_color='#F0F0F0')],
        [sg.InputText(key='-TARGET-', size=(50, 1), font=('Helvetica', 10), background_color='white'),
         sg.FolderBrowse('Browse', target='-TARGET-', button_color=('white', '#4A90E2'), font=('Helvetica', 10, 'bold'))],
        [sg.HorizontalSeparator()],
        [sg.Button('Build Plan', key='-BUILD-', button_color=('white', '#27AE60'), font=('Helvetica', 12, 'bold'), size=(15, 1))],
        [sg.Text('', key='-STATUS-', size=(60, 1), font=('Helvetica', 10, 'italic'), text_color='#E74C3C')],
        [sg.HorizontalSeparator()],
        [sg.Text('Plan Actions:', font=('Helvetica', 12, 'bold'), visible=False, key='-TABLE_LABEL-', background_color='#F0F0F0')],
        [sg.Table(values=[], headings=['#', 'Type', 'Src/SrcA', 'Dest/SrcB'], key='-TABLE-', size=(70, 10), visible=False,
                  font=('Helvetica', 9), header_font=('Helvetica', 10, 'bold'), header_background_color='#4A90E2', header_text_color='white',
                  background_color='white', alternating_row_color='#F8F8F8')],
        [sg.Checkbox('Dry run', key='-DRY_RUN-', visible=False, font=('Helvetica', 10))],
        [sg.Button('Apply Plan', key='-APPLY-', visible=False, button_color=('white', '#E67E22'), font=('Helvetica', 12, 'bold'), size=(15, 1))],
        [sg.Text('Notes & Warnings:', font=('Helvetica', 12, 'bold'), visible=False, key='-NOTES_LABEL-', background_color='#F0F0F0')],
        [sg.Multiline('', key='-NOTES-', size=(70, 5), visible=False, font=('Courier', 9), background_color='white')],
    ]

    window = sg.Window('Obsidian Bracelet - Vault Merger', layout, resizable=True, finalize=True)

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
                window['-TABLE_LABEL-'].update(visible=True)
                window['-APPLY-'].update(visible=True)
                window['-DRY_RUN-'].update(visible=True)
                notes = json.dumps({"notes": plan.get("notes", []), "warnings": plan.get("warnings", [])}, indent=2)
                window['-NOTES-'].update(notes, visible=True)
                window['-NOTES_LABEL-'].update(visible=True)
                window['-STATUS-'].update('Plan built successfully', text_color='#27AE60')
            except Exception as e:
                window['-STATUS-'].update(f'Error building plan: {e}', text_color='#E74C3C')

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
