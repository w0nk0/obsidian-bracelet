"""
Test robustness against invalid markdown formatting and front-matter issues.
"""

import json
from pathlib import Path
import pytest

from obsidian_bracelet.planner import build_plan
from obsidian_bracelet.apply import apply_plan


def test_invalid_frontmatter_handling(tmp_path: Path):
    """Test handling of files with invalid frontmatter"""
    v1 = tmp_path / "vault1"
    v2 = tmp_path / "vault2"
    target = tmp_path / "merged"
    
    # Create vault1 with invalid frontmatter
    v1.mkdir()
    (v1 / ".obsidian").mkdir()
    (v1 / ".obsidian" / "app.json").write_text("{}")
    
    # File with unclosed frontmatter
    (v1 / "invalid1.md").write_text("---\ntitle: Test\ncontent: missing closing")
    
    # File with malformed YAML in frontmatter
    (v1 / "invalid2.md").write_text("---\ntitle: Test\ninvalid: [unclosed array\n---\n\nContent")
    
    # File with frontmatter-like content but not actual frontmatter
    (v1 / "invalid3.md").write_text("This is not frontmatter\n---\nBut has dashes")
    
    # Create vault2 with valid content
    v2.mkdir()
    (v2 / ".obsidian").mkdir()
    (v2 / ".obsidian" / "app.json").write_text("{}")
    (v2 / "invalid1.md").write_text("# Valid Content\n\nSome content")
    
    # Should not crash when building plan
    plan = build_plan([v1, v2], target)
    assert plan is not None
    assert "actions" in plan
    
    # Should be able to apply plan without crashing
    apply_plan(plan)
    assert target.exists()


def test_malformed_markdown_links(tmp_path: Path):
    """Test handling of malformed markdown links"""
    v1 = tmp_path / "vault1"
    target = tmp_path / "merged"
    
    v1.mkdir()
    (v1 / ".obsidian").mkdir()
    (v1 / ".obsidian" / "app.json").write_text("{}")
    
    # File with malformed links
    (v1 / "malformed.md").write_text("""
# Malformed Links

[Unclosed link
[[Unclosed wiki link
[Text](unclosed-paren
[Text](extra-close-paren))
[[Link|extra-close-bracket]]
[Text](path/with spaces and no quotes)
[[Wiki link with spaces]]
""")
    
    # Should not crash when building plan
    plan = build_plan([v1], target)
    assert plan is not None
    
    # Should be able to apply plan
    apply_plan(plan)
    assert (target / "malformed.md").exists()


def test_unicode_and_encoding_issues(tmp_path: Path):
    """Test handling of unicode and encoding issues"""
    v1 = tmp_path / "vault1"
    target = tmp_path / "merged"
    
    v1.mkdir()
    (v1 / ".obsidian").mkdir()
    (v1 / ".obsidian" / "app.json").write_text("{}")
    
    # File with various unicode characters
    (v1 / "unicode.md").write_text("""
# Unicode Test

Emoji: 🚀 🎉 😊
Chinese: 你好世界
Arabic: مرحبا بالعالم
Russian: Привет мир
Special chars: «» "" '' — – …
""")
    
    # File with invalid UTF-8 sequences (simulate)
    (v1 / "binary.md").write_bytes(b"# Binary content\n\xff\xfe\x00Invalid UTF-8")
    
    # Should not crash when building plan
    plan = build_plan([v1], target)
    assert plan is not None
    
    # Should be able to apply plan
    apply_plan(plan)
    assert (target / "unicode.md").exists()
    assert (target / "binary.md").exists()


def test_extremely_large_files(tmp_path: Path):
    """Test handling of extremely large files"""
    v1 = tmp_path / "vault1"
    target = tmp_path / "merged"
    
    v1.mkdir()
    (v1 / ".obsidian").mkdir()
    (v1 / ".obsidian" / "app.json").write_text("{}")
    
    # Create a very large markdown file (5MB)
    large_content = "# Large File\n\n" + "This is a line.\n" * 100000
    (v1 / "large.md").write_text(large_content)
    
    # Should not crash when building plan
    plan = build_plan([v1], target)
    assert plan is not None
    
    # Should be able to apply plan
    apply_plan(plan)
    assert (target / "large.md").exists()
    
    # Verify content integrity
    copied_content = (target / "large.md").read_text(encoding="utf-8", errors="ignore")
    assert len(copied_content) > 1000000  # Should be large


def test_files_with_special_characters_in_names(tmp_path: Path):
    """Test handling of files with special characters in names"""
    v1 = tmp_path / "vault1"
    target = tmp_path / "merged"
    
    v1.mkdir()
    (v1 / ".obsidian").mkdir()
    (v1 / ".obsidian" / "app.json").write_text("{}")
    
    # Files with special characters in names
    (v1 / "file with spaces.md").write_text("# Spaces in filename")
    (v1 / "file-with-dashes.md").write_text("# Dashes in filename")
    (v1 / "file_with_underscores.md").write_text("# Underscores in filename")
    (v1 / "file.with.dots.md").write_text("# Dots in filename")
    (v1 / "file(with)parentheses.md").write_text("# Parentheses in filename")
    (v1 / "file[with]brackets.md").write_text("# Brackets in filename")
    (v1 / "file'with'quotes.md").write_text("# Quotes in filename")
    (v1 / "file&with&ampersands.md").write_text("# Ampersands in filename")
    
    # Should not crash when building plan
    plan = build_plan([v1], target)
    assert plan is not None
    
    # Should be able to apply plan
    apply_plan(plan)
    
    # Verify files were copied
    assert (target / "file with spaces.md").exists()
    assert (target / "file-with-dashes.md").exists()
    assert (target / "file_with_underscores.md").exists()


def test_empty_and_corrupted_files(tmp_path: Path):
    """Test handling of empty and corrupted files"""
    v1 = tmp_path / "vault1"
    target = tmp_path / "merged"
    
    v1.mkdir()
    (v1 / ".obsidian").mkdir()
    (v1 / ".obsidian" / "app.json").write_text("{}")
    
    # Empty file
    (v1 / "empty.md").write_text("")
    
    # File with only whitespace
    (v1 / "whitespace.md").write_text("   \n  \n   \n")
    
    # File with only frontmatter (no content)
    (v1 / "frontmatter-only.md").write_text("---\ntitle: Test\n---\n")
    
    # File with binary content disguised as markdown
    (v1 / "binary-disguised.md").write_bytes(b"# Binary\n\xff\xfe\x00\xfd")
    
    # Should not crash when building plan
    plan = build_plan([v1], target)
    assert plan is not None
    
    # Should be able to apply plan
    apply_plan(plan)
    
    # Verify files were created
    assert (target / "empty.md").exists()
    assert (target / "whitespace.md").exists()
    assert (target / "frontmatter-only.md").exists()
    assert (target / "binary-disguised.md").exists()


def test_permission_denied_graceful_handling(tmp_path: Path):
    """Test graceful handling when files can't be read during planning"""
    v1 = tmp_path / "vault1"
    target = tmp_path / "merged"
    
    v1.mkdir()
    (v1 / ".obsidian").mkdir()
    (v1 / ".obsidian" / "app.json").write_text("{}")
    
    # Create a normal file
    (v1 / "normal.md").write_text("# Normal file")
    
    # Create a file and make it unreadable (if possible)
    unreadable = v1 / "unreadable.md"
    unreadable.write_text("# Unreadable file")
    try:
        unreadable.chmod(0o000)  # Remove all permissions
    except OSError:
        # Skip this test if we can't change permissions
        pytest.skip("Cannot change file permissions on this system")
    
    try:
        # Should not crash when building plan
        plan = build_plan([v1], target)
        assert plan is not None
        
        # Should still include the readable file
        actions = plan["actions"]
        copy_actions = [a for a in actions if a["type"] == "copy"]
        assert any("normal.md" in act.get("src", "") for act in copy_actions)
        
    finally:
        # Restore permissions for cleanup
        try:
            unreadable.chmod(0o644)
        except OSError:
            pass