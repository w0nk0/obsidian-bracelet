# Contributing to Obsidian Bracelet

Thank you for your interest in contributing to Obsidian Bracelet! This document provides guidelines for contributors.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/w0nk0/obsidian-bracelet.git
   cd obsidian-bracelet
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync --extra dev
   
   # Or using pip
   pip install -e .
   pip install pytest
   ```

3. **Run tests**
   ```bash
   uv run pytest tests/ -v
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use descriptive variable and function names
- Add docstrings to new functions and classes
- Keep lines under 100 characters when possible

## Testing

- Write tests for new features
- Ensure all tests pass before submitting a pull request
- Aim for good test coverage for new code

## Submitting Changes

1. **Create a new branch** for your feature or bugfix
   ```bash
   git checkout -b feature-name
   ```

2. **Make your changes** and commit them with a clear message
   ```bash
   git commit -m "Add feature: description of change"
   ```

3. **Push to your fork** and create a pull request
   ```bash
   git push origin feature-name
   ```

## Pull Request Process

- Provide a clear description of your changes
- Link to any relevant issues
- Ensure all tests pass
- Wait for code review

## Bug Reports

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages

## Feature Requests

When requesting features, please include:
- Use case description
- Expected behavior
- Any implementation ideas

## Questions

For questions about contributing or using the project, please:
- Check existing documentation
- Search existing issues
- Create a new issue with the "question" label

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.