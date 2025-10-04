"""
Test Case Mapping for tests/test_planner.py:

Core Functionality Tests:
- test_same_content_same_names_deduplication: Corresponds to Test Case 2 in test-vaults/Test Cases.md
- test_markdown_merge_conflicts: Corresponds to Test Case 3 in test-vaults/Test Cases.md
- test_settings_merge: Corresponds to Test Case 6 in test-vaults/Test Cases.md

New Feature Tests:
- test_same_content_different_names_deduplication: Corresponds to Test Case 8 in test-vaults/Test Cases.md
- test_ignore_patterns: Corresponds to Test Case 9 in test-vaults/Test Cases.md
"""

import json
from pathlib import Path
import pytest

from obsidian_bracelet.planner import build_plan


# Test Case 2: Content-Based Deduplication (Same Names)
@pytest.fixture
def same_content_same_names(tmp_path: Path):
    """Setup for Test Case 2: Same content with same filenames"""
    v1 = tmp_path / "vault1"
    v2 = tmp_path / "vault2"
    target = tmp_path / "merged"
    for v in (v1, v2):
        (v / ".obsidian").mkdir(parents=True)
        (v / ".obsidian" / "app.json").write_text("{}")
    # Same filename, same content
    (v1 / "Shared.md").write_text("This is shared content.\nLine 2.\nLine 3.")
    (v2 / "Shared.md").write_text("This is shared content.\nLine 2.\nLine 3.")
    return [v1, v2], target


def test_same_content_same_names_deduplication(same_content_same_names):
    """Test Case 2: Content-Based Deduplication - Same filenames with identical content"""
    sources, target = same_content_same_names
    plan = build_plan(sources, target)
    actions = plan["actions"]

    # Should have only one copy action for Shared.md (deduplicated)
    shared_copy_actions = [a for a in actions if a["type"] == "copy" and "Shared.md" in a["dest"]]
    assert len(shared_copy_actions) == 1

    # Should have deduplication note
    notes = plan["notes"]
    assert any("Deduplicated identical Shared.md" in note for note in notes)


# Test Case 3: Filename Conflict Resolution
@pytest.fixture
def filename_conflicts(tmp_path: Path):
    """Setup for Test Case 3: Different content with same filenames"""
    v1 = tmp_path / "vault1"
    v2 = tmp_path / "vault2"
    target = tmp_path / "merged"
    for v in (v1, v2):
        (v / ".obsidian").mkdir(parents=True)
        (v / ".obsidian" / "app.json").write_text("{}")
    # Same filename, different content
    (v1 / "Project.md").write_text("# Project\n\nPersonal project notes.\n\n## Ideas\n- Idea 1\n- Idea 2")
    (v2 / "Project.md").write_text("# Project\n\nWork project notes.\n\n## Tasks\n- Task A\n- Task B")
    return [v1, v2], target


def test_markdown_merge_conflicts(filename_conflicts):
    """Test Case 3: Filename Conflict Resolution - Markdown merging"""
    sources, target = filename_conflicts
    plan = build_plan(sources, target)
    actions = plan["actions"]

    # Should have merge_markdown action for Project.md
    merge_actions = [a for a in actions if a["type"] == "merge_markdown" and "Project.md" in a["dest"]]
    assert len(merge_actions) == 1

    # Should have conflict note
    notes = plan["notes"]
    assert any("Proposed merge for markdown collision: Project.md" in note for note in notes)


# Test Case 6: Settings Merge
@pytest.fixture
def settings_merge_test(tmp_path: Path):
    """Setup for Test Case 6: Settings merging"""
    v1 = tmp_path / "vault1"
    v2 = tmp_path / "vault2"
    target = tmp_path / "merged"
    for v in (v1, v2):
        (v / ".obsidian").mkdir(parents=True)
        (v / ".obsidian" / "app.json").write_text('{"theme": "dark"}')
    # Add some regular files
    (v1 / "note.md").write_text("Note content")
    return [v1, v2], target


def test_settings_merge(settings_merge_test):
    """Test Case 6: Settings Merge - Obsidian configuration merging"""
    sources, target = settings_merge_test
    plan = build_plan(sources, target)
    actions = plan["actions"]

    # Should have merge_settings action
    settings_actions = [a for a in actions if a["type"] == "merge_settings"]
    assert len(settings_actions) == 1

    # Since app.json files have identical content, they should be deduplicated (not renamed)
    # Only one copy action for the deduplicated app.json
    app_copy_actions = [a for a in actions if a["type"] == "copy" and "app.json" in a["dest"]]
    assert len(app_copy_actions) == 1

    # Should have copy action for note.md
    copy_actions = [a for a in actions if a["type"] == "copy" and "note.md" in a["dest"]]
    assert len(copy_actions) == 1


# Test Case 8: Same Content in Differently Named Files
@pytest.fixture
def same_content_different_names(tmp_path: Path):
    """Setup for Test Case 8: Same content in differently named files"""
    v1 = tmp_path / "vault1"
    v2 = tmp_path / "vault2"
    target = tmp_path / "merged"
    for v in (v1, v2):
        (v / ".obsidian").mkdir(parents=True)
        (v / ".obsidian" / "app.json").write_text("{}")
    # Same content different names
    (v1 / "Ideas.md").write_text("This is an idea.\nAnother idea here.\nFinal idea.")
    (v2 / "Concepts.md").write_text("This is an idea.\nAnother idea here.\nFinal idea.")
    # Add a file that links to one of them
    (v1 / "Main.md").write_text("Main file\n\nSee [[Ideas.md]] for ideas.\nAlso check [[Concepts.md]].")
    return [v1, v2], target


def test_same_content_different_names_deduplication(same_content_different_names):
    """Test Case 8: Same Content in Differently Named Files - Deduplication"""
    sources, target = same_content_different_names
    plan = build_plan(sources, target)
    actions = plan["actions"]

    # Should have copy actions for Main.md and one of the duplicates
    md_copy_actions = [a for a in actions if a["type"] == "copy" and a["dest"].endswith(".md")]
    md_link_actions = [a for a in actions if a["type"] == "create_link_file" and a["dest"].endswith(".md")]
    link_update_actions = [a for a in actions if a["type"] == "update_file_links"]

    assert len(md_copy_actions) >= 1  # At least Main.md
    assert len(md_link_actions) == 1  # One duplicate file becomes a link
    assert len(link_update_actions) >= 0  # May have link updates if Main.md links to replaced file

    # One file should be copied (Concepts.md alphabetically first), other linked
    copy_dests = [a["dest"] for a in md_copy_actions]
    link_dest = md_link_actions[0]["dest"]
    link_to = md_link_actions[0]["link_to"]

    # Ensure Concepts.md and Ideas.md are handled (one copied, one linked)
    concepts_copied = any("Concepts.md" in dest for dest in copy_dests)
    ideas_linked = "Ideas.md" in link_dest

    assert (concepts_copied and ideas_linked) or ("Ideas.md" in str(copy_dests) and "Concepts.md" in link_dest)

    # The link should point to the copied file
    assert any(link_to in dest for dest in copy_dests)

    # Notes should include deduplication message
    notes = plan["notes"]
    assert any("Deduplicated same content" in note for note in notes)

    # No excluded files
    assert plan["excluded_files"] == []


# Test Case 9: File Exclusion with Ignore Patterns
def test_ignore_patterns(tmp_path: Path):
    """Test Case 9: File Exclusion with Ignore Patterns"""
    v1 = tmp_path / "vault1"
    v2 = tmp_path / "vault2"
    target = tmp_path / "merged"

    # Create test vaults with mixed file types
    for v in (v1, v2):
        (v / ".obsidian").mkdir(parents=True)
        (v / ".obsidian" / "app.json").write_text("{}")
        (v / "keep.md").write_text("Keep this")
        (v / "ignore.tmp").write_text("Ignore this")

    # Plan with ignore pattern for .tmp files
    plan = build_plan([v1, v2], target, ignore_patterns=[r"\.tmp$"])

    # Should exclude ignore.tmp from both vaults
    excluded = plan["excluded_files"]
    assert len(excluded) == 2  # one from each vault
    assert any("ignore.tmp" in e for e in excluded)

    # Actions should include copy for keep.md but not for ignore.tmp
    actions = plan["actions"]
    copy_dests = [a["dest"] for a in actions if a["type"] == "copy"]
    assert not any("ignore.tmp" in dest for dest in copy_dests)
    assert any("keep.md" in dest for dest in copy_dests)

    # Should also have settings actions
    settings_actions = [a for a in actions if a["type"] == "merge_settings"]
    assert len(settings_actions) == 1