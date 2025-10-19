from __future__ import annotations
import re
import shutil
import webbrowser
import datetime
from pathlib import Path
from typing import Iterable

def _ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def _copy(src: Path, dest: Path):
    _ensure_parent(dest)
    try:
        if src.suffix.lower() == '.md':
            content = src.read_text(encoding="utf-8", errors="ignore")
            content = _update_links(content)
            dest.write_text(content, encoding="utf-8")
        else:
            shutil.copy2(src, dest)
    except (OSError, PermissionError, IOError) as e:
        # Try to create a placeholder file if copy fails
        try:
            placeholder = f"# Copy Failed\n\nCould not copy {src.name}\nError: {e}"
            dest.write_text(placeholder, encoding="utf-8")
        except Exception:
            pass  # If even placeholder fails, skip silently

def _update_links(content: str) -> str:
    # Update links to files moved to !res
    def replace_link(match):
        link = match.group(2)
        if not link.startswith(('http://', 'https://', '#')) and '.' in link:
            # All non-markdown files are in !res
            path = Path(link)
            if path.suffix.lower() not in ('.md', '.txt'):
                # If link doesn't already start with !res, add it
                if not link.startswith('!res/'):
                    # For non-markdown files, we want to extract just the filename
                    # and place it directly under !res, regardless of the original path structure
                    # This ensures ../image.png becomes !res/image.png, not !res/../image.png
                    filename = path.name
                    return f'[{match.group(1)}](!res/{filename})'
        return match.group(0)
    # Update markdown links
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, content)
    # Update wiki links if they have extensions
    def replace_wiki(match):
        full_link = match.group(1)
        # Check if this is a link with an alias
        if '|' in full_link:
            # Split into link and alias
            parts = full_link.split('|', 1)
            # Check if the first part is an alias or the link
            if '.' in parts[0] and Path(parts[0]).suffix.lower() not in ('.md', '.txt'):
                # Format: [[link_path|alias]]
                link = parts[0]
                alias = parts[1]
            else:
                # Format: [[alias|link_path]]
                alias = parts[0]
                link = parts[1]
            
            if '.' in link and Path(link).suffix.lower() not in ('.md', '.txt'):
                # If link doesn't already start with !res, add it
                if not link.startswith('!res/'):
                    # For non-markdown files, we want to extract just the filename
                    # and place it directly under !res, regardless of the original path structure
                    path = Path(link)
                    filename = path.name
                    return f'[[{alias}|!res/{filename}]]'
        else:
            # No alias, use the original logic
            link = full_link
            if '.' in link and Path(link).suffix.lower() not in ('.md', '.txt'):
                # If link doesn't already start with !res, add it
                if not link.startswith('!res/'):
                    # For non-markdown files, we want to extract just the filename
                    # and place it directly under !res, regardless of the original path structure
                    path = Path(link)
                    filename = path.name
                    return f'[[!res/{filename}]]'
        return match.group(0)
    content = re.sub(r'\[\[([^\]]+)\]\]', replace_wiki, content)
    return content

def _merge_markdown(src_a: Path, src_b: Path, dest: Path, vault_a: str, vault_b: str):
    # Simple merge: frontmatter union (best-effort) + concatenate bodies with divider.
    # Placeholder MVP; a later step will implement proper frontmatter merge.
    _ensure_parent(dest)
    try:
        a = src_a.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        a = f"# Error reading {vault_a} file\n\nCould not read file: {e}"
    
    try:
        b = src_b.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        b = f"# Error reading {vault_b} file\n\nCould not read file: {e}"
    
    a = _update_links(a)
    b = _update_links(b)
    divider_a = f"\n\n---\nFrom {vault_a}\n---\n\n"
    divider_b = f"\n\n---\nFrom {vault_b}\n---\n\n"
    
    try:
        dest.write_text(divider_a + a + divider_b + b, encoding="utf-8")
    except Exception:
        # If merge fails, create individual files
        try:
            dest_a = dest.with_name(f"{dest.stem}__from-{vault_a}{dest.suffix}")
            dest_b = dest.with_name(f"{dest.stem}__from-{vault_b}{dest.suffix}")
            dest_a.write_text(a, encoding="utf-8")
            dest_b.write_text(b, encoding="utf-8")
        except Exception:
            pass  # If even individual files fail, skip silently

def _merge_settings(sources: list[Path], dest_dir: Path):
    # MVP: union known JSON files if present; later step will deepen this logic.
    dest_dir.mkdir(parents=True, exist_ok=True)
    # TODO: implement deep JSON merge for .obsidian files (app.json, core-plugins.json, community-plugins.json, hotkeys.json, etc.)

def _generate_html_report(stats: dict, plan: dict, target_root: Path) -> Path:
    """Generate an HTML report of the merge statistics."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate space saved percentage
    space_saved_pct = 0
    if stats['deduplicated_files'] > 0 and stats['deduplicated_files'] + stats['copied_files'] > 0:
        space_saved_pct = (stats['deduplicated_files'] / (stats['deduplicated_files'] + stats['copied_files'])) * 100
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Obsidian Vault Merge Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .success {{
            color: #27ae60;
        }}
        .warning {{
            color: #f39c12;
        }}
        .info {{
            color: #3498db;
        }}
        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            width: {space_saved_pct}%;
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Obsidian Vault Merge Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        
        <h2>Merge Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats.get('original_files', 0)}</div>
                <div class="stat-label">Original Files in Source Vaults</div>
            </div>
            <div class="stat-card">
                <div class="stat-number success">{stats.get('total_files', 0)}</div>
                <div class="stat-label">Files in Merged Vault</div>
            </div>
            <div class="stat-card">
                <div class="stat-number info">{stats['deduplicated_files']}</div>
                <div class="stat-label">Deduplicated Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['copied_files']}</div>
                <div class="stat-label">Unique Files Copied</div>
            </div>
        </div>
        
        <h2>Detailed Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['merged_files']}</div>
                <div class="stat-label">Merged Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['renamed_files']}</div>
                <div class="stat-label">Renamed Files (Collisions)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['link_files_created']}</div>
                <div class="stat-label">Link Files Created</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['links_updated']}</div>
                <div class="stat-label">Links Updated</div>
            </div>
        </div>
        
        {f'''<h2>Space Savings</h2>
        <div class="stat-card">
            <div class="stat-number success">{stats['deduplicated_files']} files</div>
            <div class="stat-label">Files saved through deduplication</div>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
            <div class="stat-label">{space_saved_pct:.1f}% reduction in file count</div>
        </div>''' if stats['deduplicated_files'] > 0 else ''}
        
        <h2>Source Vaults</h2>
        <ul>"""
    
    # Add source vault information
    if "sources" in plan:
        for source_path in plan["sources"]:
            source = Path(source_path)
            if source.exists():
                file_count = 0
                for p in source.rglob("*"):
                    if p.is_file() and not str(p.relative_to(source)).startswith(".obsidian/workspace"):
                        file_count += 1
                html_content += f'<li><strong>{source.name}:</strong> {file_count} files</li>'
    
    html_content += f"""
        </ul>
        
        <h2>Target Location</h2>
        <p><code>{target_root}</code></p>
        
        <footer>
            <p>Report generated by Obsidian Vault Merger</p>
        </footer>
    </div>
</body>
</html>"""
    
    # Write HTML report
    report_path = target_root / "merge_report.html"
    report_path.write_text(html_content, encoding="utf-8")
    return report_path

def apply_plan(plan: dict, dry_run: bool = False):
    actions: Iterable[dict] = plan.get("actions", [])
    
    # Statistics tracking
    stats = {
        "copied_files": 0,
        "deduplicated_files": 0,
        "merged_files": 0,
        "renamed_files": 0,
        "link_files_created": 0,
        "links_updated": 0,
        "directories_created": 0
    }
    
    for act in actions:
        t = act["type"]
        if t == "mkdir":
            if dry_run:
                continue
            Path(plan["target_root"]).mkdir(parents=True, exist_ok=True)
            stats["directories_created"] += 1
        elif t == "copy":
            src = Path(act["src"])
            dest = Path(act["dest"])
            if not dry_run:
                _copy(src, dest)
                stats["copied_files"] += 1
        elif t == "rename_copy":
            src = Path(act["src"])
            dest = Path(act["dest"])
            if not dry_run:
                _copy(src, dest)
                stats["renamed_files"] += 1
        elif t == "merge_markdown":
            src_a = Path(act["src_a"])
            src_b = Path(act["src_b"])
            dest = Path(act["dest"])
            vault_a = act.get("vault_a", "Vault A")
            vault_b = act.get("vault_b", "Vault B")
            if not dry_run:
                _merge_markdown(src_a, src_b, dest, vault_a, vault_b)
                stats["merged_files"] += 1
        elif t == "merge_settings":
            sources = [Path(s) for s in act["sources"]]
            dest_dir = Path(act["dest"])
            if not dry_run:
                _merge_settings(sources, dest_dir)
        elif t == "create_link_file":
            dest = Path(act["dest"])
            link_to = Path(act["link_to"])
            if not dry_run:
                _ensure_parent(dest)
                rel_link = link_to.relative_to(Path(plan["target_root"]))
                content = f"# Redirect\n\n[[{rel_link}]]"
                dest.write_text(content, encoding="utf-8")
                stats["link_files_created"] += 1
        elif t == "update_file_links":
            file_path = Path(act["file"])
            link_updates = act["link_updates"]
            if not dry_run and file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    updated = False
                    for old_path, new_path in link_updates.items():
                        old_rel = Path(old_path).relative_to(Path(plan["target_root"]))
                        new_rel = Path(new_path).relative_to(Path(plan["target_root"]))

                        # Update wiki links [[old_rel]] -> [[new_rel]]
                        old_wiki = f"[[{old_rel}]]"
                        new_wiki = f"[[{new_rel}]]"
                        if old_wiki in content:
                            content = content.replace(old_wiki, new_wiki)
                            updated = True

                        # Update markdown links ](old_rel) -> ](new_rel)
                        old_md = f"]({old_rel})"
                        new_md = f"]({new_rel})"
                        if old_md in content:
                            content = content.replace(old_md, new_md)
                            updated = True

                    if updated:
                        file_path.write_text(content, encoding="utf-8")
                        stats["links_updated"] += 1
                except Exception:
                    pass  # Skip if file can't be updated
        else:
            raise ValueError(f"Unknown action type: {t}")
    
    # Count deduplicated files from plan notes
    if "notes" in plan:
        for note in plan["notes"]:
            if "Deduplicated identical" in note:
                stats["deduplicated_files"] += 1
    
    # Count total files in the merged vault
    if not dry_run and "target_root" in plan:
        target_root = Path(plan["target_root"])
        if target_root.exists():
            total_files = 0
            for p in target_root.rglob("*"):
                if p.is_file():
                    total_files += 1
            
            # Count original files in source vaults
            original_files = 0
            if "sources" in plan:
                for source_path in plan["sources"]:
                    source = Path(source_path)
                    if source.exists():
                        for p in source.rglob("*"):
                            if p.is_file() and not str(p.relative_to(source)).startswith(".obsidian/workspace"):
                                original_files += 1
            
            # Add original files count to stats for the report
            stats['original_files'] = original_files
            stats['total_files'] = total_files
            
            # Generate HTML report
            report_path = _generate_html_report(stats, plan, target_root)
            
            # Print statistics
            print("\n=== Merge Statistics ===")
            print(f"Original files in source vaults: {original_files}")
            print(f"Copied files: {stats['copied_files']}")
            print(f"Deduplicated files: {stats['deduplicated_files']}")
            print(f"Merged files: {stats['merged_files']}")
            print(f"Renamed files: {stats['renamed_files']}")
            print(f"Link files created: {stats['link_files_created']}")
            print(f"Links updated: {stats['links_updated']}")
            print(f"Directories created: {stats['directories_created']}")
            print(f"Total files in merged vault: {total_files}")
            
            # Calculate space savings from deduplication
            if stats['deduplicated_files'] > 0:
                space_saved = stats['deduplicated_files']
                print(f"Space saved from deduplication: {space_saved} files")
            
            # Verify the numbers add up
            expected_total = (
                stats['copied_files'] + 
                stats['merged_files'] + 
                stats['renamed_files'] + 
                stats['link_files_created']
            )
            if expected_total != total_files:
                print(f"Warning: Expected {expected_total} files but found {total_files} in merged vault")
            else:
                print("✓ File counts match expected values")
            
            print(f"\n📄 HTML report generated: {report_path}")
            print("🌐 Opening report in browser...")
            
            # Open the report in the default browser
            try:
                webbrowser.open(f"file://{report_path.absolute()}")
            except Exception as e:
                print(f"Could not open browser: {e}")
                print(f"Please open the report manually: {report_path}")
            
            print("========================\n")
