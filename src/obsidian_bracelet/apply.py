from __future__ import annotations
import json
import re
import shutil
from pathlib import Path
from typing import Iterable

def _ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def _copy(src: Path, dest: Path):
    _ensure_parent(dest)
    if src.suffix.lower() == '.md':
        content = src.read_text(encoding="utf-8", errors="ignore")
        content = _update_links(content)
        dest.write_text(content, encoding="utf-8")
    else:
        shutil.copy2(src, dest)

def _update_links(content: str) -> str:
    # Update links to files moved to !res
    def replace_link(match):
        link = match.group(2)
        if not link.startswith(('http://', 'https://', '#')) and '.' in link:
            # Assume moved to !res if not md/txt
            path = Path(link)
            if path.suffix.lower() not in ('.md', '.txt'):
                return f'[{match.group(1)}](!res/{link})'
        return match.group(0)
    # Update markdown links
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, content)
    # Update wiki links if they have extensions
    def replace_wiki(match):
        link = match.group(1).split('|')[0]
        if '.' in link and Path(link).suffix.lower() not in ('.md', '.txt'):
            return f'[[!res/{link}]]'
        return match.group(0)
    content = re.sub(r'\[\[([^\]]+)\]\]', replace_wiki, content)
    return content

def _merge_markdown(src_a: Path, src_b: Path, dest: Path, vault_a: str, vault_b: str):
    # Simple merge: frontmatter union (best-effort) + concatenate bodies with divider.
    # Placeholder MVP; a later step will implement proper frontmatter merge.
    _ensure_parent(dest)
    a = src_a.read_text(encoding="utf-8", errors="ignore")
    b = src_b.read_text(encoding="utf-8", errors="ignore")
    a = _update_links(a)
    b = _update_links(b)
    divider_a = f"\n\n---\nFrom {vault_a}\n---\n\n"
    divider_b = f"\n\n---\nFrom {vault_b}\n---\n\n"
    dest.write_text(divider_a + a + divider_b + b, encoding="utf-8")

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
            vault_a = act.get("vault_a", "Vault A")
            vault_b = act.get("vault_b", "Vault B")
            if not dry_run:
                _merge_markdown(src_a, src_b, dest, vault_a, vault_b)
        elif t == "merge_settings":
            sources = [Path(s) for s in act["sources"]]
            dest_dir = Path(act["dest"])
            if not dry_run:
                _merge_settings(sources, dest_dir)
        else:
            raise ValueError(f"Unknown action type: {t}")
