# Title: Obsidian Bracelet - A tool to merge multiple Obsidian vaults (Release 1.0)

Hey fellow Obsidian enthusiasts! 🎉

I just wanted to share something I've been working on - a tool called **Obsidian Bracelet** that helps merge multiple Obsidian vaults together.

## What it does
- Merges multiple vaults while handling conflicts intelligently
- Deduplicates identical content (even with different filenames)
- Updates all your links automatically when files get moved or deduplicated
- Has both CLI and a simple GUI interface
- Lets you exclude files with regex patterns if needed

## Why I built it
I've got over 20 years of notes scattered across different vaults and needed a way to consolidate them without losing everything. I'll be honest - I vibe-coded a large part of the functionality, but I'm confident it works because I'm using it myself on my precious note collection!

## Features
- **Smart merging**: Handles conflicts by keeping both versions with clear attribution
- **Content deduplication**: Finds identical files and prevents duplicates
- **Link updating**: Automatically fixes links when files are moved
- **GUI**: Modern interface with a nice summary of what it's going to do
- **Ignore patterns**: Exclude files you don't want merged
- **Robust error handling**: Won't crash on weird files or permissions

## How to get it
```bash
git clone https://github.com/w0nk0/obsidian-bracelet.git
cd obsidian-bracelet
uv sync  # or pip install -e .
uv run python -m obsidian_bracelet.cli gui
```

## My honest take
This isn't some enterprise-grade software with a team of developers. It's a personal project that solves a real problem I had. I've tested it on my own 20+ years of notes, and it worked great for me. There are 24 tests passing, so the basic functionality should be solid.

## Feedback welcome!
I'd love to hear what you think! I'm happy to get feedback and bug reports, but I need to be upfront - I'll have limited time to incorporate changes into the project myself. That said, if you find something broken or have a great idea, drop it in the issues and I'll see what I can do.

## GitHub
[https://github.com/w0nk0/obsidian-bracelet](https://github.com/w0nk0/obsidian-bracelet)

Hope this helps someone else with their note chaos! 🚀