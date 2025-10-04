# Obsidian Bracelet

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-24%20passing-brightgreen.svg)
![Release](https://img.shields.io/github/release/w0nk0/obsidian-bracelet.svg)

A Python utility that intelligently merges multiple Obsidian vaults while handling conflicts, deduplicating identical content, and preserving file relationships through automatic link updating.

## Quick Start

```bash
# Install
git clone https://github.com/w0nk0/obsidian-bracelet.git
cd obsidian-bracelet
uv sync

# Basic merge
uv run python -m obsidian_bracelet.cli plan -s vault1 -s vault2 -t merged -o plan.json
uv run python -m obsidian_bracelet.cli apply plan.json

# Launch GUI
uv run python -m obsidian_bracelet.cli gui
```

## Features

- **Intelligent Merging**: Automatically detects file conflicts and merges markdown content with source attribution
- **Content Deduplication**: Detects and deduplicates identical content, even with different filenames
- **Link Updating**: Automatically updates links when files are deduplicated or moved
- **File Exclusion**: Regex-based patterns to exclude unwanted files from merging
- **Conflict Resolution**: Handles filename collisions, identical content deduplication, and settings merging
- **GUI Review**: Modern desktop GUI with plan summary and sorted operations for easy review
- **Robust Error Handling**: Gracefully manages invalid markdown, permission issues, and corrupted files
- **Dry Run Mode**: Test merges before applying changes

## Documentation

- **[HOW_TO_USE.md](HOW_TO_USE.md)** - Complete usage guide with CLI, GUI, and programmatic examples
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current implementation status and features
- **[tests/ROBUSTNESS_REPORT.md](tests/ROBUSTNESS_REPORT.md)** - Error handling and robustness analysis

## Architecture

```
obsidian-bracelet/
├── src/obsidian_bracelet/
│   ├── __init__.py
│   ├── cli.py           # Command-line interface
│   ├── planner.py       # Merge planning logic
│   ├── apply.py         # Action execution
│   └── gui.py           # Modern GUI with plan summary
├── tests/               # Comprehensive test suite (24 tests)
├── test-vaults/         # Test data and scenarios
├── docs/                # Architecture diagrams
├── HOW_TO_USE.md        # Usage guide
├── PROJECT_STATUS.md    # Implementation status
└── README.md
```

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/test_planner.py -v      # Core functionality
uv run pytest tests/test_apply.py -v       # End-to-end tests
uv run pytest tests/test_invalid_markdown.py -v  # Robustness tests
```

## Requirements

- Python 3.8 or higher
- `uv` package manager (recommended) or pip
- For GUI: Desktop environment (Linux, macOS, or Windows)

## License

See [LICENSE](LICENSE) file for details.