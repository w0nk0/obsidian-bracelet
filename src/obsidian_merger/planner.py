from __future__ import annotations
from pathlib import Path
import hashlib
from collections import defaultdict

def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def _rel_files(vault: Path):
    # All files except .obsidian/workspace.json (ephemeral)
    for p in vault.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(vault)
        if str(rel).startswith(".obsidian/workspace"):
            continue
        yield rel

def build_plan(sources: list[Path], target: Path) -> dict:
    assert sources, "At least one source vault required"
    actions = []
    notes = []
    warnings = []

    # Map relpath -> list of (vault_name, abs_path, hash)
    index = defaultdict(list)
    for s in sources:
        if not (s / ".obsidian").exists():
            warnings.append(f"{s} does not look like an Obsidian vault (missing .obsidian)")
        vname = s.name
        for rel in _rel_files(s):
            ap = s / rel
            index[str(rel)].append((vname, ap, _sha256(ap)))

    # Ensure base target dir creation
    actions.append({"type": "mkdir", "path": "."})

    for rel, entries in index.items():
        # Unique file: copy as-is
        if len(entries) == 1:
            vname, ap, _h = entries[0]
            actions.append({"type": "copy", "src": str(ap), "dest": str(Path(target) / rel)})
            continue

        # Multiple entries with same rel
        hashes = {h for _, _, h in entries}
        if len(hashes) == 1:
            # identical content: keep first
            vname, ap, _h = entries[0]
            notes.append(f"Deduplicated identical {rel} from {len(entries)} vaults; kept {vname}")
            actions.append({"type": "copy", "src": str(ap), "dest": str(Path(target) / rel)})
            continue

        # Different content: collision
        suffix_copies = []
        is_md = str(rel).lower().endswith(".md")
        if is_md and len(entries) == 2:
            # propose merge_markdown
            (v1, ap1, _), (v2, ap2, _) = entries
            dest = Path(target) / rel
            actions.append({"type": "merge_markdown", "src_a": str(ap1), "src_b": str(ap2), "dest": str(dest)})
            notes.append(f"Proposed merge for markdown collision: {rel} ({v1} vs {v2})")
        else:
            # rename copies with vault suffix
            for vname, ap, _ in entries:
                stem = Path(rel).stem
                ext = Path(rel).suffix
                renamed = Path(rel).with_name(f"{stem}__vault-{vname}{ext}")
                dest = Path(target) / renamed
                suffix_copies.append({"type": "rename_copy", "src": str(ap), "dest": str(dest)})
            actions.extend(suffix_copies)
            warnings.append(f"Collision on {rel}: proposing {len(suffix_copies)} renamed copies")

    # Basic .obsidian settings merge placeholders
    actions.append({"type": "merge_settings", "sources": [str(s) for s in sources], "dest": str(Path(target) / ".obsidian")})

    return {
        "target_root": str(target),
        "actions": actions,
        "notes": notes,
        "warnings": warnings,
        "sources": [str(s) for s in sources],
    }
