#!/usr/bin/env python3
"""
Vault Indexing Utility for Obsidian Bracelet

This module provides functionality to create index files for an Obsidian vault
based on file modification dates. It creates yearly and monthly index files
that organize links to all files in the vault.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys
import re
import yaml
from typing import Dict, List, Optional

# File type classifications
TEXT_EXTENSIONS = {
    '.md', '.txt', '.rst', '.org', '.adoc', '.asciidoc',
    '.py', '.js', '.ts', '.html', '.css', '.scss', '.less',
    '.json', '.yaml', '.yml', '.xml', '.toml',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat',
    '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs',
    '.php', '.rb', '.swift', '.kt', '.scala', '.r',
    '.sql', '.graphql', '.dockerfile'
}

MEDIA_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.webp', '.svg', '.ico', '.heic', '.heif', '.avif',
    # Videos
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
    '.m4v', '.3gp', '.ogv', '.ts', '.mts', '.m2ts',
    # Audio
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
    '.opus', '.aiff', '.au', '.ra', '.amr',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.odt', '.ods', '.odp', '.pages', '.numbers', '.key',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
    '.tar.gz', '.tar.bz2', '.tar.xz'
}

def is_text_file(file_path: Path) -> bool:
    """Check if a file is a text file based on its extension."""
    return file_path.suffix.lower() in TEXT_EXTENSIONS

def is_media_file(file_path: Path) -> bool:
    """Check if a file is a media file based on its extension."""
    return file_path.suffix.lower() in MEDIA_EXTENSIONS

def update_file_tags(file_path: Path, year_tag: str, month_tag: str) -> bool:
    """
    Add year and month tags to a markdown file if it has frontmatter.
    
    Args:
        file_path: Path to the markdown file
        year_tag: Year tag to add (e.g., "YEAR2025")
        month_tag: Month tag to add (e.g., "MONTH2025_10")
        
    Returns:
        True if the file was updated, False otherwise
    """
    if file_path.suffix.lower() != '.md':
        return False
        
    try:
        content = file_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    
    # Check if file has frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not frontmatter_match:
        return False
    
    # Parse existing frontmatter
    try:
        frontmatter_text = frontmatter_match.group(1)
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        return False
    
    # Ensure frontmatter is a dict
    if not isinstance(frontmatter, dict):
        frontmatter = {}
    
    # Get existing tags or create new list
    tags = frontmatter.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    
    # Add new tags if they don't exist
    if year_tag not in tags:
        tags.append(year_tag)
    if month_tag not in tags:
        tags.append(month_tag)
    
    # Update frontmatter
    frontmatter['tags'] = tags
    
    # Rebuild content with updated frontmatter
    new_frontmatter = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    # Remove trailing newlines from yaml dump
    new_frontmatter = new_frontmatter.rstrip()
    
    new_content = f"---\n{new_frontmatter}\n---\n" + content[frontmatter_match.end():]
    
    # Write back to file
    try:
        file_path.write_text(new_content, encoding='utf-8')
        return True
    except (OSError, PermissionError):
        return False

def collect_files(vault_path: Path) -> Dict[str, Dict[str, Dict[str, List[Dict]]]]:
    """
    Collect all files in the vault and organize them by year, month, and type.
    
    Returns:
        Nested dictionary structure:
        {
            "YYYY": {
                "YYYY_MM": {
                    "text_files": [{"path": str, "date": str, "size": int}, ...],
                    "media_files": [{"path": str, "date": str, "size": int}, ...]
                },
                ...
            },
            ...
        }
    """
    file_data = defaultdict(lambda: defaultdict(lambda: {"text_files": [], "media_files": []}))
    
    # Skip .obsidian directory and index files
    skip_patterns = {'.obsidian', 'YEAR', 'MONTH'}
    
    for file_path in vault_path.rglob("*"):
        # Skip directories and special patterns
        if file_path.is_dir():
            continue
            
        # Skip files that match our patterns or are in .obsidian
        if any(pattern in file_path.name for pattern in skip_patterns):
            continue
        if '.obsidian' in file_path.parts:
            continue
            
        # Get file stats
        try:
            stat = file_path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size
        except (OSError, PermissionError):
            continue
            
        # Get year and month
        year = mtime.strftime("%Y")
        month_key = f"{year}_{mtime.strftime('%m')}"
        
        # Get relative path
        rel_path = file_path.relative_to(vault_path)
        
        # Create file info
        file_info = {
            "path": str(rel_path),
            "date": mtime.strftime("%Y-%m-%d"),
            "size": size
        }
        
        # Categorize by type
        if is_text_file(file_path):
            file_data[year][month_key]["text_files"].append(file_info)
        elif is_media_file(file_path):
            file_data[year][month_key]["media_files"].append(file_info)
        else:
            # Treat unknown files as media
            file_data[year][month_key]["media_files"].append(file_info)
    
    # Sort files by date within each category
    for year_data in file_data.values():
        for month_data in year_data.values():
            month_data["text_files"].sort(key=lambda x: x["date"])
            month_data["media_files"].sort(key=lambda x: x["date"])
    
    return dict(file_data)

def generate_monthly_index(year: str, month_key: str, month_data: Dict, output_dir: Path) -> Path:
    """Generate a monthly index file."""
    filename = f"MONTH{month_key}.md"
    output_path = output_dir / filename
    
    # Parse month for display
    year_num, month_num = month_key.split("_")
    month_name = datetime(int(year_num), int(month_num), 1).strftime("%B %Y")
    
    # Build content
    lines = [
        f"# {month_name}",
        ""
    ]
    
    # Text files section
    if month_data["text_files"]:
        lines.extend([
            "## Text Files",
            ""
        ])
        for file_info in month_data["text_files"]:
            # Create wiki link
            file_path = Path(file_info["path"])
            wiki_link = f"[[{file_path.as_posix()}]]"
            lines.append(f"- {file_info['date']}: {wiki_link}")
        lines.append("")
    
    # Media files section
    if month_data["media_files"]:
        lines.extend([
            "## Media Files",
            ""
        ])
        for file_info in month_data["media_files"]:
            # Create wiki link
            file_path = Path(file_info["path"])
            wiki_link = f"[[{file_path.as_posix()}]]"
            size_mb = file_info["size"] / (1024 * 1024)
            lines.append(f"- {file_info['date']}: {wiki_link} ({size_mb:.2f} MB)")
        lines.append("")
    
    # Write file
    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    
    return output_path

def generate_yearly_index(year: str, year_data: Dict, output_dir: Path) -> Path:
    """Generate a yearly index file."""
    filename = f"YEAR{year}.md"
    output_path = output_dir / filename
    
    # Build content
    lines = [
        f"# {year}",
        "",
        "## Monthly Indexes",
        ""
    ]
    
    # Sort months chronologically
    sorted_months = sorted(year_data.keys(), key=lambda x: (x.split("_")[0], x.split("_")[1]))
    
    for month_key in sorted_months:
        month_file = f"MONTH{month_key}.md"
        wiki_link = f"[[{month_file}]]"
        
        # Parse month for display
        year_num, month_num = month_key.split("_")
        month_name = datetime(int(year_num), int(month_num), 1).strftime("%B")
        
        # Count files
        text_count = len(year_data[month_key]["text_files"])
        media_count = len(year_data[month_key]["media_files"])
        
        lines.append(f"- {month_name}: {wiki_link} ({text_count} text, {media_count} media files)")
    
    lines.append("")
    
    # Write file
    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    
    return output_path

def generate_indexes(vault_path: Path, output_dir: Optional[Path] = None, overwrite: bool = False, 
                         update_tags: bool = False) -> None:
    """
    Generate index files for the vault.
    
    Args:
        vault_path: Path to the vault
        output_dir: Directory to write index files (default: vault root)
        overwrite: Whether to overwrite existing index files
        update_tags: Whether to add year/month tags to files with frontmatter
    """
    if output_dir is None:
        output_dir = vault_path
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for existing index files
    existing_files = set()
    for pattern in ["YEAR*.md", "MONTH*.md"]:
        existing_files.update(output_dir.glob(pattern))
    
    if existing_files and not overwrite:
        print(f"Found {len(existing_files)} existing index files. Use --overwrite to replace them.")
        return
    
    # Collect file data
    print(f"Scanning vault: {vault_path}")
    file_data = collect_files(vault_path)
    
    if not file_data:
        print("No files found to index.")
        return
    
    # Update tags in files if requested
    if update_tags:
        print("\nUpdating tags in files...")
        updated_count = 0
        for year, year_data in file_data.items():
            year_tag = f"YEAR{year}"
            for month_key, month_data in year_data.items():
                month_tag = f"MONTH{month_key}"
                
                # Update text files
                for file_info in month_data["text_files"]:
                    file_path = vault_path / file_info["path"]
                    if update_file_tags(file_path, year_tag, month_tag):
                        updated_count += 1
        
        print(f"Updated tags in {updated_count} files.")
    
    # Generate monthly indexes
    monthly_files = []
    for year, year_data in file_data.items():
        for month_key, month_data in year_data.items():
            if month_data["text_files"] or month_data["media_files"]:
                monthly_file = generate_monthly_index(year, month_key, month_data, output_dir)
                monthly_files.append(monthly_file)
                print(f"Created: {monthly_file.name}")
    
    # Generate yearly indexes
    yearly_files = []
    for year, year_data in file_data.items():
        yearly_file = generate_yearly_index(year, year_data, output_dir)
        yearly_files.append(yearly_file)
        print(f"Created: {yearly_file.name}")
    
    print(f"\nGenerated {len(monthly_files)} monthly and {len(yearly_files)} yearly index files.")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate index files for an Obsidian vault based on modification dates"
    )
    parser.add_argument(
        "vault_path",
        type=Path,
        help="Path to the Obsidian vault"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write index files (default: vault root)",
        default=None
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing index files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing files"
    )
    parser.add_argument(
        "--update-tags",
        action="store_true",
        help="Add year/month tags to files with frontmatter"
    )
    
    args = parser.parse_args()
    
    # Validate vault path
    if not args.vault_path.exists():
        print(f"Error: Vault path does not exist: {args.vault_path}")
        sys.exit(1)
    
    if not args.vault_path.is_dir():
        print(f"Error: Vault path is not a directory: {args.vault_path}")
        sys.exit(1)
    
    # Check if it's a valid vault
    if not (args.vault_path / ".obsidian").exists():
        print(f"Warning: {args.vault_path} does not appear to be an Obsidian vault (no .obsidian directory)")
    
    if args.dry_run:
        print("DRY RUN - No files will be created")
        # Collect file data to show what would be generated
        file_data = collect_files(args.vault_path)
        if file_data:
            print("\nWould generate the following index files:")
            for year in file_data:
                print(f"  YEAR{year}.md")
                for month_key in file_data[year]:
                    if file_data[year][month_key]["text_files"] or file_data[year][month_key]["media_files"]:
                        print(f"  MONTH{month_key}.md")
        else:
            print("No files found to index.")
    else:
        generate_indexes(
            args.vault_path,
            args.output_dir,
            args.overwrite,
            args.update_tags
        )

if __name__ == "__main__":
    main()