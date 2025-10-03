from __future__ import annotations
from pathlib import Path
import json
from flask import Flask, request, render_template_string, redirect, url_for

from .planner import build_plan
from .apply import apply_plan

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Obsidian Bracelet</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        form { margin-bottom: 20px; }
        textarea, input { width: 100%; padding: 8px; margin: 5px 0; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .status { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        pre { background: #f8f8f8; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Obsidian Bracelet</h1>
    {% if status %}
    <div class="status {{ 'success' if 'Success' in status else 'error' }}">{{ status }}</div>
    {% endif %}
    <form method="post" action="/build">
        <label>Source vault paths (one per line):</label><br>
        <textarea name="sources" rows="4" required>{{ sources or '' }}</textarea><br>
        <label>Target vault path:</label><br>
        <input type="text" name="target" value="{{ target or '' }}" required><br>
        <button type="submit">Build Plan</button>
    </form>
    {% if plan_json %}
    <h2>Plan Details</h2>
    <form method="post" action="/apply">
        <input type="hidden" name="plan_json" value="{{ plan_json }}">
        <label><input type="checkbox" name="dry_run" value="1"> Dry run</label><br>
        <button type="submit">Apply Plan</button>
    </form>
    <h3>All Actions</h3>
    <table>
        <tr><th>#</th><th>Type</th><th>Src/SrcA</th><th>Dest/SrcB</th></tr>
        {% for row in all_rows %}
        <tr>
            {% for cell in row %}
            <td>{{ cell }}</td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
    {% if notes %}
    <h3>Notes & Warnings</h3>
    <pre>{{ notes }}</pre>
    {% endif %}
    {% endif %}
</body>
</html>
"""

def _path_list_from_text(text: str) -> list[Path]:
    parts = [p.strip() for p in (text or "").replace(",", "\n").splitlines() if p.strip()]
    return [Path(p).expanduser().resolve() for p in parts]

def _format_actions_by_type(plan: dict):
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

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, sources=None, target=None, plan_json=None, all_rows=[], notes=None, status=None)

@app.route("/build", methods=["POST"])
def build():
    sources_text = request.form.get("sources", "")
    target_text = request.form.get("target", "")
    sources = _path_list_from_text(sources_text)
    if not sources:
        return render_template_string(HTML_TEMPLATE, sources=sources_text, target=target_text, status="Please provide at least one source vault path.")
    if not target_text:
        return render_template_string(HTML_TEMPLATE, sources=sources_text, target=target_text, status="Please provide a target vault path.")
    target = Path(target_text).expanduser().resolve()
    plan = build_plan(sources, target)
    groups, all_rows = _format_actions_by_type(plan)
    plan_json = json.dumps(plan, indent=2, ensure_ascii=False)
    notes = json.dumps({"notes": plan.get("notes", []), "warnings": plan.get("warnings", [])}, indent=2, ensure_ascii=False)
    return render_template_string(HTML_TEMPLATE, sources=sources_text, target=target_text, plan_json=plan_json, all_rows=all_rows, notes=notes, status="Plan built successfully")

@app.route("/apply", methods=["POST"])
def apply():
    plan_json = request.form.get("plan_json", "")
    dry_run = "dry_run" in request.form
    try:
        plan = json.loads(plan_json)
        apply_plan(plan, dry_run=dry_run)
        status = "Success" + (" (dry run)" if dry_run else "")
    except Exception as e:
        status = f"Error: {e}"
    return render_template_string(HTML_TEMPLATE, status=status)

def main(source=None, target=None, plan_file=None):
    app.run(debug=True)
