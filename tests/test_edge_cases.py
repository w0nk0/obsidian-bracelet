"""
Test Case Mapping for tests/test_edge_cases.py:

- test_empty_vault: Corresponds to Test Case 7, Scenario 1 (Empty vault)
- test_invalid_vault: Corresponds to Test Case 7, Scenario 2 (Invalid vault)
- test_permission_errors: Corresponds to Test Case 7, Scenario 3 (Permission errors)
- test_large_files: Corresponds to Test Case 7, Scenario 4 (Large files)
"""

from pathlib import Path
import pytest

from obsidian_bracelet.planner import build_plan
from obsidian_bracelet.apply import apply_plan


# Test Case 7, Scenario 1: Empty vault
def test_empty_vault(tmp_path: Path):
    """Test Case 7, Scenario 1: Empty vault - Should produce warning about missing .obsidian folder"""
    empty_vault = tmp_path / "empty-vault"
    empty_vault.mkdir()  # Create empty directory without .obsidian
    
    valid_vault = tmp_path / "valid-vault"
    valid_vault.mkdir()
    (valid_vault / ".obsidian").mkdir()
    (valid_vault / ".obsidian" / "app.json").write_text("{}")
    (valid_vault / "note.md").write_text("Valid note")
    
    target = tmp_path / "merged"
    
    # Build plan with empty vault
    plan = build_plan([empty_vault, valid_vault], target)
    
    # Should have warning about not containing any Obsidian vaults
    warnings = plan["warnings"]
    assert any("does not contain any Obsidian vaults" in warning for warning in warnings)
    assert any("empty-vault" in warning for warning in warnings)
    
    # Should still have actions for valid vault
    actions = plan["actions"]
    assert len(actions) > 0
    
    # Apply plan should still work for valid vault content
    apply_plan(plan)
    assert (target / "note.md").exists()


# Test Case 7, Scenario 2: Invalid vault
def test_invalid_vault(tmp_path: Path):
    """Test Case 7, Scenario 2: Invalid vault - Directory missing .obsidian folder (filtered out early)"""
    invalid_vault = tmp_path / "invalid-vault"
    invalid_vault.mkdir()
    (invalid_vault / "note.md").write_text("Note in invalid vault")  # No .obsidian folder
    
    target = tmp_path / "merged"
    
    # Build plan with invalid vault
    plan = build_plan([invalid_vault], target)
    
    # Should have warning about not containing any Obsidian vaults
    warnings = plan["warnings"]
    assert any("does not contain any Obsidian vaults" in warning for warning in warnings)
    
    # Plan should be generated but with minimal actions
    actions = plan["actions"]
    # Should still have mkdir action for target
    mkdir_actions = [a for a in actions if a["type"] == "mkdir"]
    assert len(mkdir_actions) >= 1
    
    # Should NOT have copy actions for files in invalid vault (vault is filtered out)
    copy_actions = [a for a in actions if a["type"] == "copy"]
    assert len(copy_actions) == 0  # Should not copy any files from invalid vault


# Test Case 7, Scenario 3: Permission errors
def test_permission_errors(tmp_path: Path):
    """Test Case 7, Scenario 3: Permission errors - Should fail when trying to write to read-only target"""
    source_vault = tmp_path / "source"
    source_vault.mkdir()
    (source_vault / ".obsidian").mkdir()
    (source_vault / ".obsidian" / "app.json").write_text("{}")
    (source_vault / "note.md").write_text("Source note")
    
    target = tmp_path / "readonly-target"
    target.mkdir()
    
    # Make target directory read-only
    target.chmod(0o444)
    
    try:
        # Build plan
        plan = build_plan([source_vault], target)
        
        # Applying plan should fail due to permission error
        with pytest.raises(Exception):  # Should raise some kind of permission error
            apply_plan(plan)
            
    finally:
        # Restore permissions for cleanup
        target.chmod(0o755)


# Test Case 7, Scenario 4: Large files
def test_large_files(tmp_path: Path):
    """Test Case 7, Scenario 4: Large files - Should handle large files without issues"""
    source_vault = tmp_path / "source"
    source_vault.mkdir()
    (source_vault / ".obsidian").mkdir()
    (source_vault / ".obsidian" / "app.json").write_text("{}")
    
    # Create a large file (1MB)
    large_content = "A" * (1024 * 1024)  # 1MB of 'A' characters
    (source_vault / "large_file.md").write_text(f"# Large File\n\n{large_content}")
    
    # Create another large file with different content
    large_content_2 = "B" * (1024 * 1024)  # 1MB of 'B' characters
    (source_vault / "another_large.md").write_text(f"# Another Large File\n\n{large_content_2}")
    
    target = tmp_path / "merged"
    
    # Build and apply plan
    plan = build_plan([source_vault], target)
    apply_plan(plan)
    
    # Verify large files were copied correctly
    assert (target / "large_file.md").exists()
    assert (target / "another_large.md").exists()
    
    # Verify content integrity
    copied_content = (target / "large_file.md").read_text()
    assert len(copied_content) > 1024 * 1024  # Should be larger than 1MB
    assert "A" * 100 in copied_content  # Sample check
    
    copied_content_2 = (target / "another_large.md").read_text()
    assert len(copied_content_2) > 1024 * 1024  # Should be larger than 1MB
    assert "B" * 100 in copied_content_2  # Sample check


# Test Case 7, Scenario 4: Large files with merge
def test_large_files_merge(tmp_path: Path):
    """Test Case 7, Scenario 4: Large files with merging - Should handle large file merges"""
    v1 = tmp_path / "vault1"
    v2 = tmp_path / "vault2"
    target = tmp_path / "merged"
    
    # Create vaults with large files having same name but different content
    for i, vault in enumerate([v1, v2]):
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        (vault / ".obsidian" / "app.json").write_text("{}")
        
        # Create large file (500KB each)
        large_content = f"Content from vault {i+1}\n" + "X" * (500 * 1024)
        (vault / "large_note.md").write_text(f"# Large Note {i+1}\n\n{large_content}")
    
    # Build and apply plan
    plan = build_plan([v1, v2], target)
    apply_plan(plan)
    
    # Verify large files were merged correctly
    assert (target / "large_note.md").exists()
    
    merged_content = (target / "large_note.md").read_text()
    assert "Content from vault 1" in merged_content
    assert "Content from vault 2" in merged_content
    assert "---" in merged_content  # Divider should be present
    assert len(merged_content) > 1000 * 1024  # Should be larger than 1MB total