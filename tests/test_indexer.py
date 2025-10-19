"""Tests for the vault indexing utility."""

import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_bracelet.indexer import collect_files, generate_monthly_index, generate_yearly_index

def test_collect_files():
    """Test file collection and categorization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test files
        (tmpdir / ".obsidian").mkdir()
        (tmpdir / "text.md").write_text("# Test")
        (tmpdir / "script.py").write_text("print('hello')")
        (tmpdir / "data.csv").write_text("a,b\n1,2")
        (tmpdir / "image.png").write_bytes(b"fake image")
        
        # Set modification dates (different dates to test sorting)
        import os
        import time
        now = time.time()
        os.utime(tmpdir / "text.md", (now - 86400, now - 86400))  # 1 day ago
        os.utime(tmpdir / "script.py", (now - 172800, now - 172800))  # 2 days ago
        os.utime(tmpdir / "data.csv", (now, now))  # Now
        os.utime(tmpdir / "image.png", (now - 259200, now - 259200))  # 3 days ago
        
        # Collect files
        created_data, modified_data = collect_files(tmpdir)
        
        # Check structure
        assert len(created_data) == 1  # All files in the same year/month
        
        year = list(created_data.keys())[0]
        month_key = list(created_data[year].keys())[0]
        month_data = created_data[year][month_key]
        
        # Check text files
        assert len(month_data["text_files"]) == 2
        text_paths = [f["path"] for f in month_data["text_files"]]
        assert "text.md" in text_paths
        assert "script.py" in text_paths
        
        # Check media files
        assert len(month_data["media_files"]) == 2
        media_paths = [f["path"] for f in month_data["media_files"]]
        assert "data.csv" in media_paths
        assert "image.png" in media_paths
        
        # Check sorting (should be sorted by date)
        dates = [f["date"] for f in month_data["text_files"]]
        assert dates == sorted(dates)

def test_generate_monthly_index():
    """Test monthly index file generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        month_data = {
            "text_files": [
                {"path": "note1.md", "date": "2025-10-15", "size": 1024},
                {"path": "note2.md", "date": "2025-10-10", "size": 2048}
            ],
            "media_files": [
                {"path": "image.png", "date": "2025-10-05", "size": 1024000}
            ]
        }
        
        # Generate index
        output_path = generate_monthly_index("2025", "2025_10", month_data, tmpdir)
        
        # Check file was created
        assert output_path.exists()
        assert output_path.name == "MONTH2025_10.md"
        
        # Check content
        content = output_path.read_text()
        assert "# October 2025" in content
        assert "tags:" not in content  # Should not have tags in index files
        assert "## Text Files" in content
        assert "## Media Files" in content
        assert "[[note1.md]]" in content
        assert "[[note2.md]]" in content
        assert "[[image.png]]" in content
        assert "(0.98 MB)" in content  # Size should be displayed in MB

def test_generate_yearly_index():
    """Test yearly index file generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        year_data = {
            "2025_10": {
                "text_files": [{"path": "note.md"}],
                "media_files": [{"path": "image.png"}]
            },
            "2025_11": {
                "text_files": [{"path": "note2.md"}],
                "media_files": []
            }
        }
        
        # Generate index
        output_path = generate_yearly_index("2025", year_data, tmpdir)
        
        # Check file was created
        assert output_path.exists()
        assert output_path.name == "YEAR2025.md"
        
        # Check content
        content = output_path.read_text()
        assert "# 2025" in content
        assert "tags:" not in content  # Should not have tags in index files
        assert "## Monthly Indexes" in content
        assert "[[YEAR2025_10.md]]" in content
        assert "[[YEAR2025_11.md]]" in content
        assert "October:" in content
        assert "November:" in content
        assert "(1 text, 1 media files)" in content
        assert "(1 text, 0 media files)" in content

def test_skip_obsidian_files():
    """Test that .obsidian files are skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create .obsidian directory with files
        (tmpdir / ".obsidian").mkdir()
        (tmpdir / ".obsidian" / "app.json").write_text("{}")
        (tmpdir / ".obsidian" / "plugins.txt").write_text("")
        
        # Create regular file
        (tmpdir / "note.md").write_text("# Test")
        
        # Collect files
        created_data, modified_data = collect_files(tmpdir)
        
        # Should only have the regular file
        year = list(created_data.keys())[0]
        month_key = list(created_data[year].keys())[0]
        month_data = created_data[year][month_key]
        
        assert len(month_data["text_files"]) == 1
        assert month_data["text_files"][0]["path"] == "note.md"
        assert len(month_data["media_files"]) == 0

if __name__ == "__main__":
    test_collect_files()
    test_generate_monthly_index()
    test_generate_yearly_index()
    test_skip_obsidian_files()
    print("All tests passed!")