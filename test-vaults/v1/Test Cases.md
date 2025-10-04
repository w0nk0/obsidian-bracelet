# Test Cases for Obsidian Vault Merger

## Overview
This document outlines test cases for validating the obsidian-bracelet functionality using the provided test data in `test-vaults/`.

## Test Data Structure
- **Personal Vault** (`test-vaults/personal-vault/`): Personal notes, health tracking, books, etc.
- **Work Vault** (`test-vaults/work-vault/`): Work-related notes, meetings, technical documentation
- **Same Content Different Names** (`test-vaults/same-content-different-names/`): Test vaults with identical content in differently named files
- **Target Vault** (`test-vaults/merged-vault/`): Where merged content will be placed

## Test Case 1: Basic Vault Merging
**Objective**: Test merging two vaults with distinct content.

**Input Files**:
- `test-vaults/personal-vault/` contains: Books to Read.md, Daily Routines.md, Health Tracking.md, Project Ideas.md, 2024-10-01.md, 2024-10-02.md, Travel Plans.md, data.csv, .obsidian/app.json
- `test-vaults/work-vault/` contains: Team Meeting Notes.md, Project Ideas.md, Health Tracking.md, API Documentation.md, 2024-10-01.md, 2024-10-02.md, System Architecture.md, Final Testing Report.md, .obsidian/app.json

**Expected Output File Structure**:
After applying, `test-vaults/merged-vault/` should contain exactly these files:

```
test-vaults/merged-vault/
├── Books to Read.md
├── Daily Routines.md
├── Travel Plans.md
├── data.csv
├── Team Meeting Notes.md
├── API Documentation.md
├── System Architecture.md
├── Final Testing Report.md
├── Health Tracking.md          (merged content from both vaults)
├── Project Ideas.md            (merged content from both vaults)
├── 2024-10-01.md               (merged content from both vaults)
├── 2024-10-02.md               (merged content from both vaults)
└── .obsidian/
    ├── app__vault-personal-vault.json
    └── app__vault-work-vault.json
```

**Files that should NOT be present**: None additional (this is a complete list)

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/personal-vault -s test-vaults/work-vault -t test-vaults/merged-vault -o test-plan-basic.json
uv run python -m obsidian_bracelet.cli apply test-plan-basic.json
```

**Validation**:
- Check `test-vaults/merged-vault/` contains exactly the files listed above
- Verify merged files (Health Tracking.md, Project Ideas.md, 2024-10-01.md, 2024-10-02.md) contain content from both vaults separated by dividers
- Confirm no other files exist in the target directory

## Test Case 2: Content-Based Deduplication
**Objective**: Test that identical content with same filenames is deduplicated properly.

**Input Files**:
- Same as Test Case 1 (files that exist in both vaults with identical content)

**Expected Output File Structure**:
Same as Test Case 1 - no additional files should be created for identical content.

**Expected Behavior**:
- Files with identical content and same name should be deduplicated (kept once)
- Plan notes should indicate deduplication occurred

**Files that should NOT be present**: Same as Test Case 1

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/personal-vault -s test-vaults/work-vault -t test-vaults/merged-vault -o test-plan-basic.json
```

**Validation**:
- Check plan notes for deduplication messages
- Verify target vault structure matches Test Case 1 exactly

## Test Case 3: Filename Conflict Resolution
**Objective**: Test merging notes with same filenames but different content.

**Input Files**:
- Focus on `Project Ideas.md` and `Health Tracking.md` (exist in both vaults with different content)

**Expected Output File Structure**:
Same as Test Case 1, with the key difference that `Project Ideas.md` and `Health Tracking.md` should contain merged content from both vaults.

**Expected Behavior**:
- Plan should show `merge_markdown` actions for conflicting files
- Merged files should contain content from both vaults separated by dividers

**Files that should NOT be present**: Same as Test Case 1

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/personal-vault -s test-vaults/work-vault -t test-vaults/merged-vault -o test-plan-conflicts.json
uv run python -m obsidian_bracelet.cli apply test-plan-conflicts.json
```

**Validation**:
- Check `test-plan-conflicts.json` contains `merge_markdown` actions for `Project Ideas.md` and `Health Tracking.md`
- Verify merged files contain content from both personal and work vaults with "---" dividers

## Test Case 4: Daily Notes Merging
**Objective**: Test merging daily notes with same dates from different contexts.

**Input Files**:
- Focus on `2024-10-01.md` and `2024-10-02.md` (exist in both vaults with different content)

**Expected Output File Structure**:
Same as Test Case 1, with daily notes containing merged content.

**Expected Behavior**:
- Plan should show `merge_markdown` actions for daily notes
- Merged daily notes should contain content from both vaults with clear separation

**Files that should NOT be present**: Same as Test Case 1

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/personal-vault -s test-vaults/work-vault -t test-vaults/merged-vault -o test-plan-daily.json
uv run python -m obsidian_bracelet.cli apply test-plan-daily.json
```

**Validation**:
- Check plan contains `merge_markdown` actions for `2024-10-01.md` and `2024-10-02.md`
- Verify merged daily notes contain content from both personal and work contexts with dividers

## Test Case 5: GUI Review Process
**Objective**: Test the GUI functionality for reviewing merge plans.

**Input Files**:
- Use a generated plan JSON from Test Case 3 or 4

**Expected Behavior**:
- GUI should load and display the merge plan
- User should be able to review different types of actions in the table
- Apply button should work with dry-run option

**Expected Output File Structure**:
After GUI apply, target vault should match the structure from Test Case 3 or 4 used.

**Files that should NOT be present**: Same as the corresponding test case

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli gui --plan-file test-plan-conflicts.json
```

**Validation**:
- GUI window opens and displays plan actions in table format
- Apply button executes successfully (check target vault matches expected structure)

## Test Case 6: Settings Merge
**Objective**: Test merging of Obsidian configuration files.

**Input Files**:
- `.obsidian/app.json` from both personal-vault and work-vault (both contain "{}")

**Expected Output File Structure**:
Same as Test Case 1, with `.obsidian/` containing renamed settings files.

**Expected Behavior**:
- Plan should show `merge_settings` action
- Settings files should be renamed with vault suffixes since they have same names

**Files that should NOT be present**: Same as Test Case 1

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/personal-vault -s test-vaults/work-vault -t test-vaults/merged-vault -o test-plan-settings.json
```

**Validation**:
- Check plan contains `merge_settings` action
- Verify `.obsidian/` directory contains `app__vault-personal-vault.json` and `app__vault-work-vault.json`

## Test Case 7: Edge Cases
**Objective**: Test various edge cases and error conditions.

**Scenario 1: Empty vault**
- **Input Files**: Empty directory without `.obsidian` folder
- **Expected Behavior**: Should produce warning about missing `.obsidian` folder
- **Expected Output**: No files created, warnings in plan

**Scenario 2: Invalid vault**
- **Input Files**: Directory missing `.obsidian` folder
- **Expected Behavior**: Should produce warning about invalid vault structure
- **Expected Output**: Plan generated but with warnings, no merge actions

**Scenario 3: Permission errors**
- **Input Files**: Valid vaults
- **Expected Behavior**: Should fail when trying to write to read-only target
- **Expected Output**: Error during apply phase

**Scenario 4: Large files**
- **Input Files**: Files larger than typical test data
- **Expected Behavior**: Should handle large files without issues
- **Expected Output**: Successful merge with large files copied

## Test Case 8: Same Content in Differently Named Files
**Objective**: Test deduplication of files with identical content but different filenames.

**Input**:
- Source 1: `test-vaults/same-content-different-names/vault1/`
- Source 2: `test-vaults/same-content-different-names/vault2/`
- Target: `test-vaults/same-content-different-names/merged/`

**Input Files**:
- `test-vaults/same-content-different-names/vault1/Ideas.md`: Contains "This is an idea.\nAnother idea here.\nFinal idea."
- `test-vaults/same-content-different-names/vault2/Concepts.md`: Contains identical content "This is an idea.\nAnother idea here.\nFinal idea."
- Both vaults have `.obsidian/app.json` with "{}"

**Expected Output File Structure**:
After applying, `test-vaults/same-content-different-names/merged/` should contain exactly these files:

```
test-vaults/same-content-different-names/merged/
├── Concepts.md          (contains: "This is an idea.\nAnother idea here.\nFinal idea.")
├── Ideas.md             (contains: "# Redirect\n\n[[Concepts.md]]")
└── .obsidian/
    └── app.json         (contains: "{}")
```

**Files that should NOT be present**: None additional (this is a complete list)

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/same-content-different-names/vault1 -s test-vaults/same-content-different-names/vault2 -t test-vaults/same-content-different-names/merged -o test-plan-deduplication.json
uv run python -m obsidian_bracelet.cli apply test-plan-deduplication.json
```

**Validation**:
- Check `test-plan-deduplication.json` contains `create_link_file` action and "Deduplicated same content" note
- Check `test-vaults/same-content-different-names/merged/Concepts.md` contains the full 3-line content
- Check `test-vaults/same-content-different-names/merged/Ideas.md` contains only "# Redirect\n\n[[Concepts.md]]"

## Test Case 9: File Exclusion with Ignore Patterns
**Objective**: Test excluding files from merging using regex patterns.

**Input Files**:
- `test-vaults/personal-vault/` contains: Books to Read.md, Daily Routines.md, Health Tracking.md, Project Ideas.md, 2024-10-01.md, 2024-10-02.md, Travel Plans.md, data.csv, .obsidian/app.json
- `test-vaults/work-vault/` contains: Team Meeting Notes.md, Project Ideas.md, Health Tracking.md, API Documentation.md, 2024-10-01.md, 2024-10-02.md, System Architecture.md, Final Testing Report.md, .obsidian/app.json
- Ignore pattern: `\.md$` (excludes all markdown files)

**Expected Output File Structure**:
After applying, `test-vaults/merged-vault/` should contain exactly these files:

```
test-vaults/merged-vault/
├── data.csv
└── .obsidian/
    ├── app__vault-personal-vault.json
    └── app__vault-work-vault.json
```

**Files that should NOT be present**:
- Any `.md` files (Books to Read.md, Daily Routines.md, Health Tracking.md, Project Ideas.md, 2024-10-01.md, 2024-10-02.md, Travel Plans.md, Team Meeting Notes.md, API Documentation.md, System Architecture.md, Final Testing Report.md)
- Any other files not listed above

**Command to Test**:
```bash
uv run python -m obsidian_bracelet.cli plan -s test-vaults/personal-vault -s test-vaults/work-vault -t test-vaults/merged-vault -i "\\.md$" -o test-plan-ignore.json
uv run python -m obsidian_bracelet.cli apply test-plan-ignore.json
```

**Validation**:
- Check `test-plan-ignore.json` has `excluded_files` array listing all 15 `.md` files from both vaults
- Verify no `copy` or `merge_markdown` actions for `.md` files in the plan
- Confirm `test-vaults/merged-vault/` contains only `data.csv` and `.obsidian/` directory with renamed `app.json` files
- Confirm no `.md` files exist in `test-vaults/merged-vault/`

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
rm -rf test-vaults/same-content-different-names/merged/*
rm test-plan-*.json
```

## Notes
- These test cases cover the main functionality described in the WARP.md
- Real-world usage would involve much larger vaults with more complex conflicts
- GUI testing requires a desktop environment
- Consider adding more test cases for specific scenarios you encounter