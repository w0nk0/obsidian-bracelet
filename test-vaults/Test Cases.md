# Test Cases for Obsidian Vault Merger

## Overview
This document outlines test cases for validating the obsidian-bracelet functionality using the provided test data in `test-vaults/`.

## Test Data Structure
- **Personal Vault** (`test-vaults/personal-vault/`): Personal notes, health tracking, books, etc.
- **Work Vault** (`test-vaults/work-vault/`): Work-related notes, meetings, technical documentation
- **Target Vault** (`test-vaults/merged-vault/`): Where merged content will be placed

## Test Case 1: Basic Vault Merging
**Objective**: Test merging two vaults with distinct content.

**Input**:
- Source 1: `test-vaults/personal-vault/`
- Source 2: `test-vaults/work-vault/`
- Target: `test-vaults/merged-vault/`

**Expected Behavior**:
- All unique files should be copied to target vault
- No conflicts should occur for unique filenames
- Directory structure should be preserved
- Obsidian configuration files should be merged

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/personal-vault -s test-vaults/work-vault -t test-vaults/merged-vault -o test-plan-basic.json
```

## Test Case 2: Content-Based Deduplication
**Objective**: Test that identical content is deduplicated properly.

**Input**:
- Same vaults as Test Case 1

**Expected Behavior**:
- Files with identical content should only be copied once
- Plan should show notes about deduplication
- Target vault should not have duplicate content

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli apply test-plan-basic.json --dry-run
```

## Test Case 3: Filename Conflict Resolution
**Objective**: Test merging notes with same filenames but different content.

**Input**:
- Focus on files: `Project Ideas.md`, `Health Tracking.md`

**Expected Behavior**:
- Should generate `merge_markdown` actions for these files
- Personal and work versions should be combined with content dividers
- Result should contain content from both vaults

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/personal-vault -s test-vaults/work-vault -t test-vaults/merged-vault -o test-plan-conflicts.json
```

## Test Case 4: Daily Notes Merging
**Objective**: Test merging daily notes with same dates from different contexts.

**Input**:
- Focus on files: `2024-10-01.md`, `2024-10-02.md`

**Expected Behavior**:
- Should create `merge_markdown` actions for daily notes
- Personal and work activities should be combined
- Clear separation between personal and work content

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli apply test-plan-conflicts.json
```

## Test Case 5: GUI Review Process
**Objective**: Test the GUI functionality for reviewing merge plans.

**Input**:
- Use plan from Test Case 3 or 4

**Expected Behavior**:
- GUI should load and display the merge plan
- User should be able to review different types of actions:
  - `copy` actions (unique files)
  - `merge_markdown` actions (conflicts)
  - `mkdir` actions (directory creation)
- Apply button should work with dry-run option

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli gui --plan-file test-plan-conflicts.json
```

## Test Case 6: Settings Merge
**Objective**: Test merging of Obsidian configuration files.

**Input**:
- `.obsidian/app.json` files from both source vaults

**Expected Behavior**:
- Should create `merge_settings` action
- Configuration files should be combined appropriately
- Target vault should have valid Obsidian configuration

## Test Case 7: Edge Cases
**Objective**: Test various edge cases and error conditions.

**Scenarios to Test**:
1. **Empty vault**: Try merging with an empty directory
2. **Invalid vault**: Try merging with a directory missing `.obsidian` folder
3. **Permission errors**: Try merging to a read-only location
4. **Large files**: Test with bigger files if needed

## Validation Steps
After running tests:

1. **Check file counts**: Verify expected number of files in target
2. **Check content**: Manually review merged files for correct content
3. **Check structure**: Ensure directory structure is preserved
4. **Check conflicts**: Verify conflict resolution looks correct
5. **Test Obsidian**: Open target vault in Obsidian to ensure it works

## Cleanup
After testing, you can remove test files:
```bash
rm -rf test-vaults/merged-vault/*
rm test-plan-*.json
```

## Notes
- These test cases cover the main functionality described in the WARP.md
- Real-world usage would involve much larger vaults with more complex conflicts
- GUI testing requires a desktop environment
- Consider adding more test cases for specific scenarios you encounter