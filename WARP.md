# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.
``

Project overview
- Purpose: Integrate multiple Obsidian vaults into a new merged vault with conflict-aware planning, optional GUI review, and an apply step.
- Package: obsidian_bracelet (src layout)
- Tooling: uv-managed environment, pytest, ruff, mypy, hatchling build backend
- Entry points (after install):
  - obsidian-bracelet-merge -> obsidian_bracelet.cli:main (Typer CLI)
  - obsidian-bracelet-merge-gui -> obsidian_bracelet.gui:main (PySimpleGUI GUI)

Environment and dependencies (use uv)
- Create/sync venv from pyproject and optional dev extras:
  - uv sync --all-extras --dev
- Run commands in the environment:
  - uv run <command>
- Add a dev dependency (example):
  - uv add --dev <package>

Common development commands
- Run the CLI without installing the package:
  - uv run python -m obsidian_bracelet.cli --help
  - uv run python -m obsidian_bracelet.cli plan -s /path/to/vaultA -s /path/to/vaultB -t /path/to/merged -o merge-plan.json
  - uv run python -m obsidian_bracelet.cli apply merge-plan.json
  - uv run python -m obsidian_bracelet.cli gui -s /path/to/vaultA -s /path/to/vaultB -t /path/to/merged
- Launch the GUI (after install, console script available):
  - uv run obsidian-bracelet-merge-gui
  Notes: GUI uses PySimpleGUI and requires a desktop session. Prefer the CLI for headless use.
- Tests (pytest):
  - Run all tests: uv run pytest
  - Run with coverage: uv run pytest --cov=obsidian_bracelet --cov-report=term-missing
  - Run a single test: uv run pytest tests/test_version.py::test_version -q
- Lint and format (ruff):
  - Check: uv run ruff check src tests
  - Fix: uv run ruff check --fix src tests
- Type-check (mypy):
  - uv run mypy src
- Build (wheel/sdist via hatchling):
  - uvx hatchling build
  - Artifacts will be in ./dist/

High-level architecture
- CLI (Typer) — src/obsidian_bracelet/cli.py
  - Commands:
    - plan: Scans one or more source vaults and produces a JSON merge plan file.
    - apply: Applies a previously generated plan to the target location.
    - gui: Convenience launcher that delegates to the GUI module.
- Planner — src/obsidian_bracelet/planner.py
  - Traverses each source vault, ignoring ephemeral .obsidian/workspace* files.
  - Builds an index of relative paths to (vault_name, absolute_path, sha256) tuples.
  - Emits a plan dict with:
    - target_root: Target vault directory
    - actions: Ordered list of file operations (see below)
    - notes: Informational messages (e.g., deduplications)
    - warnings: Potential collisions or ambiguous merges
    - sources: Original vault roots
  - Collision handling:
    - Identical content across vaults -> single copy action + note
    - Two differing markdown files -> merge_markdown action proposal
    - Other differing files or >2 markdown variants -> rename_copy actions per vault with a suffix
  - Always includes mkdir for the target root and a merge_settings placeholder for .obsidian settings.
- Apply engine — src/obsidian_bracelet/apply.py
  - Executes the plan’s actions. Supports dry-run at the command level.
  - Operations:
    - mkdir: Ensure target root exists
    - copy/rename_copy: Copy files, preserving metadata
    - merge_markdown: MVP concatenation with a divider (placeholder for smarter merges)
    - merge_settings: Placeholder to union/merge Obsidian config JSONs (future expansion)
- GUI — src/obsidian_bracelet/gui.py (PySimpleGUI)
  - Loads or builds a plan, displays actions in a table, shows JSON details for a selected action, and triggers apply with optional dry-run.
- Package metadata — src/obsidian_bracelet/__init__.py
  - Exposes __version__ used by tests.

Plan schema (MVP)
- target_root: string (absolute path to target directory)
- sources: list[string] (absolute paths to source vaults)
- actions: list[object] where each action is one of:
  - {"type": "mkdir", "path": "."}
  - {"type": "copy", "src": "/abs/src", "dest": "/abs/dest"}
  - {"type": "rename_copy", "src": "/abs/src", "dest": "/abs/dest_with_suffix"}
  - {"type": "merge_markdown", "src_a": "/abs/a.md", "src_b": "/abs/b.md", "dest": "/abs/merged.md"}
  - {"type": "merge_settings", "sources": ["/abs/vaultA", "/abs/vaultB", ...], "dest": "/abs/target/.obsidian"}
- notes: list[string]
- warnings: list[string]

Conventions and important details
- Environment management: Prefer uv for creating and running the virtual environment in this repo.
- Tests: Pytest config sets quiet mode (-q) via pyproject. Keep tests under tests/.
- Ruff: Configured in pyproject (line length 100, target Python 3.10). Use ruff check and optionally --fix.
- Python version: requires >=3.10 (see pyproject).
- GUI vs CLI: If no display is available, use the CLI commands. The GUI is a thin wrapper over the same plan/apply logic.

Release checklist (informational)
- Build: uvx hatchling build
- Install locally for sanity check: uv pip install --force-reinstall dist/*.whl
- Verify console scripts: uv run obsidian-bracelet-merge --help
