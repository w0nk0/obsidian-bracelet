from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Iterable

def _ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def _copy(src: Path, dest: Path):
    _ensure_parent(dest)
    shutil.copy2(src, dest)

def _merge_markdown(src_a: Path, src_b: Path, dest: Path):
    # Simple merge: frontmatter union (best-effort) + concatenate bodies with divider.
    # Placeholder MVP; a later step will implement proper frontmatter merge.
    _ensure_parent(dest)
    a = src_a.read_text(encoding="utf-8", errors="ignore")
    b = src_b.read_text(encoding="utf-8", errors="ignore")
    divider = "\n\n---\nMerged Content Divider (keep or edit)\n---\n\n"
    dest.write_text(a + divider + b, encoding="utf-8")

def _merge_settings(sources: list[Path], dest_dir: Path):
    # MVP: union known JSON files if present; later step will deepen this logic.
    dest_dir.mkdir(parents=True, exist_ok=True)
    # TODO: implement deep JSON merge for .obsidian files (app.json, core-plugins.json, community-plugins.json, hotkeys.json, etc.)

def apply_plan(plan: dict, dry_run: bool = False):
    actions: Iterable[dict] = plan.get("actions", [])
    for act in actions:
        t = act["type"]
        if t == "mkdir":
            if dry_run: continue
            Path(plan["target_root"]).mkdir(parents=True, exist_ok=True)
        elif t in ("copy", "rename_copy"):
            src = Path(act["src"])
            dest = Path(act["dest"])
            if not dry_run:
                _copy(src, dest)
        elif t == "merge_markdown":
            src_a = Path(act["src_a"])
            src_b = Path(act["src_b"])
            dest = Path(act["dest"])
            if not dry_run:
                _merge_markdown(src_a, src_b, dest)
        elif t == "merge_settings":
            sources = [Path(s) for s in act["sources"]]
            dest_dir = Path(act["dest"])
            if not dry_run:
                _merge_settings(sources, dest_dir)
        else:
            raise ValueError(f"Unknown action type: {t}")
