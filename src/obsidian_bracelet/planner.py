from __future__ import annotations
from pathlib import Path
import hashlib
import re
from collections import defaultdict
import sys
from typing import List, Optional

def _sha256(p: Path) -> str:
    try:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError, IOError):
        # Return a hash based on filename and size if file can't be read
        try:
            stat_info = p.stat()
            return hashlib.sha256(f"{p.name}_{stat_info.st_size}".encode()).hexdigest()
        except (OSError, PermissionError, IOError):
            # Fallback to filename only
            return hashlib.sha256(p.name.encode()).hexdigest()

def _rel_files(vault: Path):
    # All files except .obsidian/workspace.json (ephemeral)
    for p in vault.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(vault)
        if str(rel).startswith(".obsidian/workspace"):
            continue
        yield rel

def _extract_links(content: str) -> set[str]:
    links = set()
    # Wiki links [[link]]
    for match in re.finditer(r'\[\[([^\]]+)\]\]', content):
        link = match.group(1).split('|')[0].strip()  # handle aliases
        links.add(link)
    # Markdown links [text](link)
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        link = match.group(2).strip()
        if not link.startswith(('http://', 'https://', '#')):  # relative links
            links.add(link)
    return links

def build_plan(sources: list[Path], target: Path, ignore_patterns: list[str] = None, verbose_output: Optional[List[str]] = None) -> dict:
    """
    Build a merge plan for the given source vaults.
    
    Args:
        sources: List of source vault paths
        target: Target vault path
        ignore_patterns: List of regex patterns to ignore
        verbose_output: Optional list to capture verbose planning output
        
    Returns:
        Dictionary containing the plan
    """
    if ignore_patterns is None:
        ignore_patterns = []
    assert sources, "At least one source vault required"
    actions = []
    notes = []
    warnings = []
    excluded = []
    
    # Helper function to either print to stderr or capture to list
    def log(message: str):
        if verbose_output is not None:
            verbose_output.append(message)
        else:
            print(message, file=sys.stderr)

    # Expand sources to include subdirectories that are vaults
    expanded_sources = []
    for s in sources:
        if (s / ".obsidian").exists():
            # This is a vault
            expanded_sources.append(s)
        else:
            # Check if this is a parent directory containing vaults
            found_vaults = False
            for item in s.iterdir():
                if item.is_dir() and (item / ".obsidian").exists():
                    expanded_sources.append(item)
                    found_vaults = True
                    log(f"  Found vault subdirectory: {item}")
            if not found_vaults:
                warnings.append(f"{s} does not contain any Obsidian vaults (no subdirectories with .obsidian)")
    
    sources = expanded_sources
    
    log(f"[ Planning phase: Starting merge plan for {len(sources)} vault(s) ]")
    log(f"  Target directory: {target}")
    for i, s in enumerate(sources, 1):
        log(f"  Source vault {i}: {s}")
    if ignore_patterns:
        log(f"  Ignore patterns: {', '.join(ignore_patterns)}")
    log("")

    # Map relpath -> list of (vault_name, abs_path, hash)
    index = defaultdict(list)
    total_files = 0
    for s in sources:
        if not (s / ".obsidian").exists():
            warnings.append(f"{s} does not look like an Obsidian vault (missing .obsidian)")
        vname = s.name
        vault_files = 0
        for rel in _rel_files(s):
            skip = False
            for pattern in ignore_patterns:
                if re.search(pattern, str(rel)):
                    excluded.append(f"{vname}:{str(rel)}")
                    skip = True
                    break
            if skip:
                continue
            ap = s / rel
            try:
                index[str(rel)].append((vname, ap, _sha256(ap)))
                vault_files += 1
                total_files += 1
            except Exception as e:
                warnings.append(f"Skipping {vname}:{str(rel)} due to error: {e}")
                continue
        log(f"  Scanned {vname}: {vault_files} files")

    log(f"  Total files scanned: {total_files}")
    log(f"  Unique files to process: {len(index)}")
    log("")
    log("[ Planning phase: Processing files ]")

    # Ensure base target dir creation
    actions.append({"type": "mkdir", "path": "."})

    unique_files = 0
    deduplicated_files = 0
    merged_files = 0
    collision_files = 0

    for rel, entries in index.items():
        # Determine if this is a markdown file
        is_md = str(rel).lower().endswith(".md")
        
        # For non-markdown files (except .obsidian files), place them in !res directory
        if not is_md and not str(rel).startswith(".obsidian/"):
            rel = Path("!res") / rel
        
        # Unique file: copy as-is
        if len(entries) == 1:
            vname, ap, _h = entries[0]
            actions.append({"type": "copy", "src": str(ap), "dest": str(Path(target) / rel)})
            unique_files += 1
            continue

        # Multiple entries with same rel
        hashes = {h for _, _, h in entries}
        if len(hashes) == 1:
            # identical content: keep first
            vname, ap, _h = entries[0]
            notes.append(f"Deduplicated identical {rel} from {len(entries)} vaults; kept {vname}")
            actions.append({"type": "copy", "src": str(ap), "dest": str(Path(target) / rel)})
            deduplicated_files += 1
            continue

        # Different content: collision
        suffix_copies = []
        if is_md and len(entries) == 2:
            # propose merge_markdown
            (v1, ap1, _), (v2, ap2, _) = entries
            dest = Path(target) / rel
            actions.append({"type": "merge_markdown", "src_a": str(ap1), "src_b": str(ap2), "dest": str(dest), "vault_a": v1, "vault_b": v2})
            notes.append(f"Proposed merge for markdown collision: {rel} ({v1} vs {v2})")
            merged_files += 1
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
            collision_files += len(suffix_copies)

    log(f"  Files processed: {unique_files} unique, {deduplicated_files} deduplicated, {merged_files} merged, {collision_files} with collisions")
    log("")
    log("[ Planning phase: Processing linked files ]")

    # Collect linked files to copy
    planned_files = {Path(act["dest"]).relative_to(target) for act in actions if "dest" in act and act["type"] in ("copy", "rename_copy", "merge_markdown")}
    for act in actions:
        if act["type"] == "merge_markdown":
            planned_files.add(Path(act["dest"]).relative_to(target))

    linked_to_copy = set()
    linked_files_count = 0
    for rel, entries in index.items():
        if not str(rel).lower().endswith(".md"):
            continue
        for vname, ap, _ in entries:
            try:
                content = ap.read_text(encoding="utf-8", errors="ignore")
                links = _extract_links(content)
                for link in links:
                    link_path = Path(link)
                    if link_path.suffix:  # has extension, assume file
                        # Find if exists in any vault
                        for s in sources:
                            full_link = s / link_path
                            if full_link.exists() and full_link.is_file():
                                # All non-markdown files are already in !res directory
                                if link_path.suffix.lower() in ('.md', '.txt'):
                                    rel_link = link_path
                                else:
                                    rel_link = Path("!res") / link_path
                                if rel_link not in planned_files:
                                    linked_to_copy.add((str(full_link), str(Path(target) / rel_link)))
                                    planned_files.add(rel_link)
                                    linked_files_count += 1
                                break
            except Exception:
                pass  # ignore read errors

    log(f"  Found {linked_files_count} linked files to copy")

    # Add linked files to actions
    for src, dest in linked_to_copy:
        actions.append({"type": "copy", "src": src, "dest": dest})

    # Basic .obsidian settings merge placeholders
    actions.append({"type": "merge_settings", "sources": [str(s) for s in sources], "dest": str(Path(target) / ".obsidian")})

    log("")
    log("[ Planning phase: Deduplicating files with identical content ]")

    # Deduplicate same content across different names
    dest_hashes = {}
    for act in actions:
        if act["type"] == "copy":
            h = _sha256(Path(act["src"]))
            dest_hashes[act["dest"]] = h

    hash_to_dests = defaultdict(list)
    for dest, h in dest_hashes.items():
        hash_to_dests[h].append(dest)

    replaced_files = {}  # old_path -> new_path
    duplicate_count = 0
    for h, dests in hash_to_dests.items():
        if len(dests) > 1:
            # Sort by path depth (shorter path first) to keep the file higher in folder structure
            dests.sort(key=lambda d: len(Path(d).relative_to(target).parts))
            kept = dests[0]
            for d in dests[1:]:
                replaced_files[d] = kept
                duplicate_count += 1
                for act in actions:
                    if act.get("dest") == d and act["type"] == "copy":
                        # Check if this is a text file (markdown or txt)
                        dest_path = Path(d)
                        is_text_file = dest_path.suffix.lower() in ('.md', '.txt')
                        
                        # Check if the kept file is in !res and the duplicate is not
                        # If so, remove the duplicate from non-!res location
                        kept_in_res = "!res/" in kept
                        dup_in_res = "!res/" in d
                        if kept_in_res and not dup_in_res:
                            # Remove the duplicate action entirely
                            actions.remove(act)
                        elif is_text_file:
                            # For text files, create a link file
                            act["type"] = "create_link_file"
                            act["link_to"] = kept
                            del act["src"]
                            rel_d = Path(d).relative_to(target)
                            rel_kept = Path(kept).relative_to(target)
                            notes.append(f"Deduplicated same content: {rel_d} -> {rel_kept}")
                        else:
                            # For non-text files, just remove the duplicate action
                            actions.remove(act)
                            rel_d = Path(d).relative_to(target)
                            rel_kept = Path(kept).relative_to(target)
                            notes.append(f"Deduplicated non-text file: {rel_d} -> {rel_kept}")
                        break

    print(f"  Found {duplicate_count} files with identical content", file=sys.stderr)

    # Update links that point to replaced files
    if replaced_files:
        print("", file=sys.stderr)
        print("[ Planning phase: Updating links to deduplicated files ]", file=sys.stderr)
        updated_files = 0
        # Find all actions that copy files that might contain links
        for act in actions:
            if act["type"] in ("copy", "merge_markdown") and act.get("dest", "").endswith(".md"):
                src_path = act.get("src")
                if src_path and Path(src_path).exists():
                    try:
                        content = Path(src_path).read_text(encoding="utf-8", errors="ignore")
                        needs_update = False
                        for old_path, new_path in replaced_files.items():
                            old_rel = Path(old_path).relative_to(target)
                            # Check for wiki links [[old_rel]] or markdown links [text](old_rel)
                            if f"[[{old_rel}]]" in content or f"]({old_rel})" in content:
                                needs_update = True
                                break
                        if needs_update:
                            # Add an update_links action for this file
                            actions.append({
                                "type": "update_file_links",
                                "file": act["dest"],
                                "link_updates": {old_path: new_path for old_path, new_path in replaced_files.items()}
                            })
                            updated_files += 1
                    except Exception:
                        pass  # Skip files that can't be read
        print(f"  Will update links in {updated_files} files", file=sys.stderr)

    print("", file=sys.stderr)
    print("[ Planning phase: Summary ]", file=sys.stderr)
    print(f"  Total actions planned: {len(actions)}", file=sys.stderr)
    print(f"  Notes: {len(notes)}", file=sys.stderr)
    print(f"  Warnings: {len(warnings)}", file=sys.stderr)
    print(f"  Excluded files: {len(excluded)}", file=sys.stderr)
    print("", file=sys.stderr)

    return {
        "target_root": str(target),
        "actions": actions,
        "notes": notes,
        "warnings": warnings,
        "sources": [str(s) for s in sources],
        "excluded_files": excluded,
    }
