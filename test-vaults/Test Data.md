# Test Data for Obsidian Vault Merger

## Overview
This directory contains realistic test data for testing the obsidian-bracelet functionality.

## Test Vaults

### Personal Vault (`personal-vault/`)
**Purpose**: Simulates a personal knowledge base and life management system.

**Content**:
- `Daily Routines.md` - Personal habits and routines
- `Health Tracking.md` - Personal health goals and metrics
- `Project Ideas.md` - Personal project concepts and learning goals
- `Books to Read.md` - Reading list and progress
- `Travel Plans.md` - Travel planning and budget
- `2024-10-01.md` - Personal daily log
- `2024-10-02.md` - Personal daily log
- `.obsidian/app.json` - Obsidian configuration

### Work Vault (`work-vault/`)
**Purpose**: Simulates a professional knowledge base and work documentation.

**Content**:
- `Team Meeting Notes.md` - Meeting summaries and action items
- `API Documentation.md` - Technical documentation
- `System Architecture.md` - Technical architecture notes
- `Project Ideas.md` - **OVERLAPPING** - Work project planning
- `Health Tracking.md` - **OVERLAPPING** - Corporate wellness program
- `2024-10-01.md` - **OVERLAPPING** - Work daily log
- `2024-10-02.md` - **OVERLAPPING** - Work daily log
- `.obsidian/app.json` - Different Obsidian configuration

### Merged Vault (`merged-vault/`)
**Purpose**: Target location for merged content.

## Test Scenarios Covered

### 1. Unique Content Merging
- Files that exist only in one vault should be copied directly
- Examples: `Daily Routines.md`, `Books to Read.md`, `Team Meeting Notes.md`

### 2. Filename Conflicts with Different Content
- Files with same names but different content should be merged
- Examples: `Project Ideas.md`, `Health Tracking.md`
- Expected: `merge_markdown` actions in plan

### 3. Identical Filename with Context Separation
- Daily notes with same dates should be merged
- Examples: `2024-10-01.md`, `2024-10-02.md`
- Expected: Clear separation between personal and work content

### 4. Configuration Merging
- Obsidian settings should be combined
- Different themes and configurations should be preserved

## Usage

Run the test cases using the commands in `Test Cases.md`:

```bash
# Generate merge plan
uv run python -m obsidian_bracelet.cli plan \
  -s test-vaults/personal-vault \
  -s test-vaults/work-vault \
  -t test-vaults/merged-vault \
  -o test-merge-plan.json

# Review plan
uv run python -m obsidian_bracelet.cli gui --plan-file test-merge-plan.json

# Apply merge
uv run python -m obsidian_bracelet.cli apply test-merge-plan.json
```

## Expected Merge Behavior

### For `Project Ideas.md`:
- Should create merged file with content from both vaults
- Clear divider between personal and work project ideas

### For Daily Notes:
- Should combine personal and work activities for same dates
- Maintain context separation between life and work

### For Unique Files:
- Should copy directly without modification
- Preserve all metadata and structure

This test data provides realistic scenarios for validating the vault merger's conflict resolution and content combination capabilities.