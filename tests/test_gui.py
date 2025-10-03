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
    groups, all_rows = _format_actions_by_type(sample_plan)
    assert any(r[1] == "merge_markdown" for r in all_rows)
    assert any(r[1] == "rename_copy" for r in all_rows)
    assert any(r[1] == "copy" for r in all_rows)
    assert any(r[1] == "merge_settings" for r in all_rows)
    assert any(r[1] == "mkdir" for r in all_rows)
    assert len(groups["copy"]) == 1


def test_build_plan_action_validates_inputs(tmp_path: Path):
    # Missing inputs should produce a status message
    outputs = build_plan_action("", "")
    # plan_json, all_table, details, status, md_table, rename_table, settings_table, copy_table
    assert isinstance(outputs, tuple) and len(outputs) == 8
    status = outputs[3]
    assert "Please provide" in status


def test_build_plan_action_success(tmp_path: Path):
    # Prepare two simple vaults
    va = tmp_path / "A"; vb = tmp_path / "B"; tgt = tmp_path / "T"
    for s in (va, vb):
        (s / ".obsidian").mkdir(parents=True, exist_ok=True)
        (s / "n.md").write_text("x")
    plan_json, all_table, details, status, md_table, rename_table, settings_table, copy_table = build_plan_action(
        f"{va}\n{vb}", str(tgt)
    )
    assert status == ""
    assert isinstance(plan_json, str) and plan_json.strip().startswith("{")
    assert isinstance(all_table, list)
    # Ensure copy_table is present (there will be actions even for mkdir/settings)
    assert isinstance(copy_table, list)
