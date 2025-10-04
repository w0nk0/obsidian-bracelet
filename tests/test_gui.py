"""
Test Case Mapping for tests/test_gui.py:

- test_format_actions_groups_markdown_and_rename: General GUI functionality test
- test_build_plan_action_validates_inputs: GUI input validation test
- test_build_plan_action_success: Corresponds to Test Case 1 in test-vaults/Test Cases.md (Basic Vault Merging)
"""

import json
from pathlib import Path
import types

import pytest

from obsidian_bracelet.gui import _format_actions_by_type, build_plan_action


@pytest.fixture
def sample_plan(tmp_path: Path):
    # Build a synthetic plan
    target = tmp_path / "merged"
    sources = [tmp_path / "vaultA", tmp_path / "vaultB"]
    for s in sources:
        (s / ".obsidian").mkdir(parents=True, exist_ok=True)
        (s / "Note.md").write_text("A")
    plan = {
        "target_root": str(target),
        "sources": [str(s) for s in sources],
        "notes": ["example"],
        "warnings": ["collision on Note.md"],
        "actions": [
            {"type": "mkdir", "path": "."},
            {"type": "merge_markdown", "src_a": str(sources[0]/"Note.md"), "src_b": str(sources[1]/"Note.md"), "dest": str(target/"Note.md")},
            {"type": "copy", "src": str(sources[0]/"file.txt"), "dest": str(target/"file.txt")},
            {"type": "rename_copy", "src": str(sources[1]/"img.png"), "dest": str(target/"img__vault-vaultB.png")},
            {"type": "merge_settings", "sources": [str(sources[0]), str(sources[1])], "dest": str(target/".obsidian")},
        ],
    }
    return plan


def test_format_actions_groups_markdown_and_rename(sample_plan):
    """Test GUI action formatting - general functionality"""
    all_rows = _format_actions_by_type(sample_plan)
    assert any(r[1] == "merge_markdown" for r in all_rows)
    assert any(r[1] == "rename_copy" for r in all_rows)
    assert any(r[1] == "copy" for r in all_rows)
    assert any(r[1] == "merge_settings" for r in all_rows)
    assert any(r[1] == "mkdir" for r in all_rows)
    assert len([r for r in all_rows if r[1] == "copy"]) == 1


def test_build_plan_action_validates_inputs(tmp_path: Path):
    """Test GUI plan building - input validation"""
    # Missing inputs should produce a status message
    outputs = build_plan_action("", "")
    # plan_json, all_table, details, status, md_table, rename_table, settings_table, copy_table
    assert isinstance(outputs, tuple) and len(outputs) == 8
    status = outputs[3]
    assert "Please provide" in status


def test_build_plan_action_success(tmp_path: Path):
    """Test GUI plan building - corresponds to Test Case 1: Basic Vault Merging"""
    # Prepare two simple vaults
    va = tmp_path / "A"; vb = tmp_path / "B"; tgt = tmp_path / "T"
    for s in (va, vb):
        (s / ".obsidian").mkdir(parents=True, exist_ok=True)
        (s / ".obsidian" / "app.json").write_text("{}")
        (s / "n.md").write_text("x")
    plan_json, all_table, details, status, md_table, rename_table, settings_table, copy_table = build_plan_action(
        f"{va}\n{vb}", str(tgt)
    )
    assert status == ""
    assert isinstance(plan_json, str) and plan_json.strip().startswith("{")
    assert isinstance(all_table, list)
    # Ensure copy_table is present (there will be actions even for mkdir/settings)
    assert isinstance(copy_table, list)

    # Verify plan contains expected elements like Test Case 1
    plan_data = json.loads(plan_json)
    assert "actions" in plan_data
    assert "notes" in plan_data
    assert "warnings" in plan_data
    assert "excluded_files" in plan_data
    assert len(plan_data["actions"]) > 0  # Should have at least mkdir action


def test_gui_review_process_test_case_5(tmp_path: Path):
    """Test Case 5: GUI Review Process - Test GUI functionality for reviewing merge plans"""
    
    # Create vaults with conflicts to generate a complex plan
    va = tmp_path / "vaultA"
    vb = tmp_path / "vaultB"
    tgt = tmp_path / "target"
    
    # Setup vault A
    va.mkdir()
    (va / ".obsidian").mkdir()
    (va / ".obsidian" / "app.json").write_text('{"theme": "dark"}')
    (va / "Project.md").write_text("# Project\n\nPersonal project notes")
    (va / "Daily.md").write_text("# Daily Note\n\nPersonal content")
    (va / "Unique.md").write_text("# Unique\n\nOnly in vault A")
    
    # Setup vault B with conflicts
    vb.mkdir()
    (vb / ".obsidian").mkdir()
    (vb / ".obsidian" / "app.json").write_text('{"theme": "light"}')
    (vb / "Project.md").write_text("# Project\n\nWork project notes")
    (vb / "Daily.md").write_text("# Daily Note\n\nWork content")
    (vb / "Work.md").write_text("# Work\n\nOnly in vault B")
    
    # Build plan using the same function GUI would use
    plan_json, all_table, details, status, md_table, rename_table, settings_table, copy_table = build_plan_action(
        f"{va}\n{vb}", str(tgt)
    )
    
    # Verify GUI can load and display the merge plan
    assert status == ""  # Plan should build successfully
    assert isinstance(all_table, list) and len(all_table) > 0
    
    # Verify different types of actions are displayed in the table
    action_types = [row[1] for row in all_table]  # Second column is action type
    assert "merge_markdown" in action_types  # Conflicting files
    assert "copy" in action_types  # Unique files
    assert "merge_settings" in action_types  # Settings files
    
    # Verify merge_markdown actions are present for conflicts
    merge_rows = [row for row in all_table if row[1] == "merge_markdown"]
    assert len(merge_rows) >= 2  # Should have at least Project.md and Daily.md
    
    # Verify copy actions for unique files
    copy_rows = [row for row in all_table if row[1] == "copy"]
    copy_files = [row[2] for row in copy_rows]  # Third column is src path
    assert any("Unique.md" in f for f in copy_files)
    assert any("Work.md" in f for f in copy_files)
    
    # Verify settings merge action
    settings_rows = [row for row in all_table if row[1] == "merge_settings"]
    assert len(settings_rows) >= 1
    
    # Verify plan details are formatted for display
    assert isinstance(details, str) and len(details) > 0
    
    # Verify plan JSON is valid and contains expected structure
    plan_data = json.loads(plan_json)
    assert "actions" in plan_data
    assert "notes" in plan_data
    assert "warnings" in plan_data
    assert "excluded_files" in plan_data
    
    # Verify the plan contains the expected actions
    actions = plan_data["actions"]
    merge_actions = [a for a in actions if a["type"] == "merge_markdown"]
    assert len(merge_actions) >= 2  # Project.md and Daily.md
    
    copy_actions = [a for a in actions if a["type"] == "copy"]
    assert len(copy_actions) >= 2  # Unique.md and Work.md
    
    # This test verifies GUI can handle the same plan that would be used in Test Case 5
    # The actual GUI display testing would require a desktop environment
