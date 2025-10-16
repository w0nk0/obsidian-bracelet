"""
Test Case Mapping for tests/test_apply.py:

- test_apply_basic_merge: Corresponds to Test Case 1 in test-vaults/Test Cases.md (Basic Vault Merging)
- test_apply_daily_notes_merge: Corresponds to Test Case 4 in test-vaults/Test Cases.md (Daily Notes Merging)
"""

from pathlib import Path
import pytest

from obsidian_bracelet.planner import build_plan
from obsidian_bracelet.apply import apply_plan


# Test Case 1: Basic Vault Merging
@pytest.fixture
def basic_vault_setup(tmp_path: Path):
    """Setup for Test Case 1: Basic Vault Merging"""
    personal_vault = tmp_path / "personal-vault"
    work_vault = tmp_path / "work-vault"
    target_vault = tmp_path / "merged-vault"
    
    # Create personal vault
    personal_vault.mkdir()
    (personal_vault / ".obsidian").mkdir()
    (personal_vault / ".obsidian" / "app.json").write_text("{}")
    (personal_vault / "Books to Read.md").write_text("# Books to Read\n\n- Book 1\n- Book 2")
    (personal_vault / "Daily Routines.md").write_text("# Daily Routines\n\nMorning routine")
    (personal_vault / "Health Tracking.md").write_text("# Health Tracking\n\nWeight: 70kg")
    (personal_vault / "Project Ideas.md").write_text("# Project Ideas\n\n- Project A\n- Project B")
    (personal_vault / "2024-10-01.md").write_text("# 2024-10-01\n\nPersonal daily note")
    (personal_vault / "2024-10-02.md").write_text("# 2024-10-02\n\nPersonal daily note")
    (personal_vault / "Travel Plans.md").write_text("# Travel Plans\n\nTrip to Paris")
    (personal_vault / "data.csv").write_text("name,age\nJohn,30")
    
    # Create work vault
    work_vault.mkdir()
    (work_vault / ".obsidian").mkdir()
    (work_vault / ".obsidian" / "app.json").write_text("{}")
    (work_vault / "Team Meeting Notes.md").write_text("# Team Meeting\n\nDiscussed project timeline")
    (work_vault / "Project Ideas.md").write_text("# Project Ideas\n\n- Project X\n- Project Y")
    (work_vault / "Health Tracking.md").write_text("# Health Tracking\n\nExercise: Running")
    (work_vault / "API Documentation.md").write_text("# API Documentation\n\nEndpoint: /api/users")
    (work_vault / "2024-10-01.md").write_text("# 2024-10-01\n\nWork daily note")
    (work_vault / "2024-10-02.md").write_text("# 2024-10-02\n\nWork daily note")
    (work_vault / "System Architecture.md").write_text("# System Architecture\n\nMicroservices design")
    (work_vault / "Final Testing Report.md").write_text("# Testing Report\n\nAll tests passed")
    
    return [personal_vault, work_vault], target_vault


def test_apply_basic_merge(basic_vault_setup):
    """Test Case 1: Basic Vault Merging - End-to-end test"""
    sources, target = basic_vault_setup
    
    # Build plan
    plan = build_plan(sources, target)
    
    # Apply plan
    apply_plan(plan)
    
    # Verify target structure
    assert target.exists()
    assert (target / "Books to Read.md").exists()
    assert (target / "Daily Routines.md").exists()
    assert (target / "Travel Plans.md").exists()
    assert (target / "!res" / "data.csv").exists()
    assert (target / "Team Meeting Notes.md").exists()
    assert (target / "API Documentation.md").exists()
    assert (target / "System Architecture.md").exists()
    assert (target / "Final Testing Report.md").exists()
    
    # Verify merged files contain content from both vaults
    health_content = (target / "Health Tracking.md").read_text()
    assert "Weight: 70kg" in health_content
    assert "Exercise: Running" in health_content
    assert "---" in health_content  # Divider between content
    
    project_content = (target / "Project Ideas.md").read_text()
    assert "Project A" in project_content
    assert "Project X" in project_content
    assert "---" in project_content
    
    # Verify daily notes are merged
    daily1_content = (target / "2024-10-01.md").read_text()
    assert "Personal daily note" in daily1_content
    assert "Work daily note" in daily1_content
    assert "---" in daily1_content
    
    # Verify .obsidian directory exists (settings merge creates directory but doesn't copy files yet)
    assert (target / ".obsidian").exists()
    # Note: Settings merge is currently a placeholder that only creates the directory
    # The actual file renaming and copying of settings files is not implemented yet


# Test Case 4: Daily Notes Merging
@pytest.fixture
def daily_notes_setup(tmp_path: Path):
    """Setup for Test Case 4: Daily Notes Merging"""
    v1 = tmp_path / "vault1"
    v2 = tmp_path / "vault2"
    target = tmp_path / "merged"
    
    # Create vault1 with daily notes
    v1.mkdir()
    (v1 / ".obsidian").mkdir()
    (v1 / ".obsidian" / "app.json").write_text("{}")
    (v1 / "2024-10-01.md").write_text("# 2024-10-01\n\nPersonal: Had coffee, went for a walk")
    (v1 / "2024-10-02.md").write_text("# 2024-10-02\n\nPersonal: Meeting with friends")
    (v1 / "Other Note.md").write_text("# Other\n\nSome other content")
    
    # Create vault2 with same daily notes but different content
    v2.mkdir()
    (v2 / ".obsidian").mkdir()
    (v2 / ".obsidian" / "app.json").write_text("{}")
    (v2 / "2024-10-01.md").write_text("# 2024-10-01\n\nWork: Team standup, code review")
    (v2 / "2024-10-02.md").write_text("# 2024-10-02\n\nWork: Project planning session")
    (v2 / "Work Note.md").write_text("# Work\n\nWork-related content")
    
    return [v1, v2], target


def test_apply_daily_notes_merge(daily_notes_setup):
    """Test Case 4: Daily Notes Merging - Verify daily notes are properly merged"""
    sources, target = daily_notes_setup
    
    # Build plan
    plan = build_plan(sources, target)
    
    # Apply plan
    apply_plan(plan)
    
    # Verify daily notes are merged with proper content
    daily1_content = (target / "2024-10-01.md").read_text()
    assert "Personal: Had coffee" in daily1_content
    assert "Work: Team standup" in daily1_content
    assert "---" in daily1_content
    
    daily2_content = (target / "2024-10-02.md").read_text()
    assert "Personal: Meeting with friends" in daily2_content
    assert "Work: Project planning session" in daily2_content
    assert "---" in daily2_content
    
    # Verify other files are copied
    assert (target / "Other Note.md").exists()
    assert (target / "Work Note.md").exists()
    
    # Verify .obsidian directory
    assert (target / ".obsidian").exists()