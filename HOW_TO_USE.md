# Obsidian Bracelet - Vault Merger

Obsidian Bracelet is a utility that intelligently merges multiple Obsidian vaults while handling conflicts, deduplicating identical content, and preserving file relationships through automatic link updating.

## Preparation

### Prerequisites
- Python 3.8 or higher
- `uv` package manager (recommended) or pip

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd obsidian-vault-integrator

# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Usage Modes

### 1. Command Line Interface (CLI)

#### Basic Merging
```bash
# Plan a merge
uv run python -m obsidian_bracelet.cli plan -s /path/to/vault1 -s /path/to/vault2 -t /path/to/target -o plan.json

# Apply the plan
uv run python -m obsidian_bracelet.cli apply plan.json
```

#### With Ignore Patterns
```bash
# Exclude files matching regex patterns
uv run python -m obsidian_bracelet.cli plan -s /path/to/vault1 -s /path/to/vault2 -t /path/to/target -i "\\.tmp$" -i "backup/.*" -o plan.json
```

#### GUI Mode
```bash
# Launch GUI
uv run python -m obsidian_bracelet.cli gui

# Or load a specific plan in GUI
uv run python -m obsidian_bracelet.cli gui --plan-file plan.json
```

### 2. Graphical User Interface (GUI)

1. **Launch the GUI**:
   ```bash
   uv run python -m obsidian_bracelet.cli gui
   ```

2. **Add Source Vaults**: Click "Add Source Folder" to select vault directories to merge

3. **Set Target Vault**: Click "Browse" to select the destination directory

4. **Configure Ignore Patterns** (optional): Enter regex patterns to exclude files (e.g., `\.tmp$, backup/.*`)

5. **Build Plan**: Click "Build Plan" to generate the merge strategy

6. **Review Plan**: Examine the actions table and notes/warnings

7. **Apply Merge**: 
   - Enable "Dry run" to test without making changes
   - Click "Apply Plan" to execute the merge

### 3. Programmatic Usage

```python
from obsidian_bracelet.planner import build_plan
from obsidian_bracelet.apply import apply_plan
from pathlib import Path

# Define vaults
sources = [Path("/path/to/vault1"), Path("/path/to/vault2")]
target = Path("/path/to/target")

# Build plan with ignore patterns
plan = build_plan(sources, target, ignore_patterns=[r"\.tmp$", r"backup/.*"])

# Apply plan
apply_plan(plan)
```

## Key Features

- **Conflict Resolution**: Automatically merges conflicting markdown files with clear separators
- **Content Deduplication**: Detects and deduplicates identical content, even with different filenames
- **Link Updating**: Automatically updates links when files are deduplicated or moved
- **File Exclusion**: Regex-based patterns to exclude unwanted files from merging
- **Settings Handling**: Merges Obsidian configuration files safely
- **Dry Run Mode**: Test merges before applying changes

## Testing

Run the test suite to verify functionality:

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test cases
uv run pytest tests/test_planner.py::test_same_content_different_names_deduplication -v
uv run pytest tests/test_apply.py::test_apply_basic_merge -v
```

## Troubleshooting

- **Missing .obsidian folder**: The system will warn but still process files
- **Permission errors**: Ensure write access to target directory
- **Large vaults**: Use dry-run mode first to preview changes
- **Complex conflicts**: Review generated plan before applying