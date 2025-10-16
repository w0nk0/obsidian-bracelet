"""Tests for the updated vault indexing utility with creation/modification tracking."""

import tempfile
from pathlib import Path
import sys
import os
import time
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_bracelet.indexer import collect_files, generate_monthly_index, generate_yearly_index

def test_collect_files_creation_modification():
    """Test file collection with both creation and modification dates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test files
        (tmpdir / ".obsidian").mkdir()
        (tmpdir / "text.md").write_text("# Test")
        (tmpdir / "script.py").write_text("print('hello')")
        (tmpdir / "data.csv").write_text("a,b\n1,2")
        (tmpdir / "image.png").write_bytes(b"fake image")
        
        # Set different creation and modification dates
        now = time.time()
        day_ago = now - 86400
        two_days_ago = now - 172800
        
        # Set creation dates
        os.utime(tmpdir / "text.md", (two_days_ago, two_days_ago))
        os.utime(tmpdir / "script.py", (day_ago, day_ago))
        os.utime(tmpdir / "data.csv", (two_days_ago, two_days_ago))
        os.utime(tmpdir / "image.png", (day_ago, day_ago))
        
        # Set modification dates (all to now)
        os.utime(tmpdir / "text.md", (now, now))
        os.utime(tmpdir / "script.py", (now, now))
        os.utime(tmpdir / "data.csv", (now, now))
        os.utime(tmpdir / "image.png", (now, now))
        
        # Collect files
        created_data, modified_data = collect_files(tmpdir)
        
        # Check structure
        assert len(created_data) == 1  # All files created in the same year/month
        assert len(modified_data) == 1  # All files modified in the same year/month
        
        # Check created data
        created_year = list(created_data.keys())[0]
        created_month_key = list(created_data[created_year].keys())[0]
        created_month_data = created_data[created_year][created_month_key]
        
        # Check modified data
        modified_year = list(modified_data.keys())[0]
        modified_month_key = list(modified_data[modified_year].keys())[0]
        modified_month_data = modified_data[modified_year][modified_month_key]
        
        # Verify data structure
        assert len(created_month_data["text_files"]) == 2
        assert len(created_month_data["media_files"]) == 2
        assert len(modified_month_data["text_files"]) == 2
        assert len(modified_month_data["media_files"]) == 2

def test_generate_monthly_index_with_prefix():
    """Test monthly index file generation with custom prefix."""
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
        
        # Generate CREATED index
        output_path = generate_monthly_index("2025", "2025_10", month_data, tmpdir, prefix="CREATED")
        
        # Check file was created
        assert output_path.exists()
        assert output_path.name == "CREATED2025_10.md"
        
        # Check content
        content = output_path.read_text()
        assert "# October 2025" in content
        assert "## Text Files" in content
        assert "## Media Files" in content
        assert "[[note1.md]]" in content
        assert "[[note2.md]]" in content
        assert "[[image.png]]" in content
        assert "(0.98 MB)" in content  # Size should be displayed in MB

def test_generate_yearly_index_with_prefix():
    """Test yearly index file generation with custom prefix."""
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
        
        # Generate MODIFIED index
        output_path = generate_yearly_index("2025", year_data, tmpdir, prefix="MODIFIED")
        
        # Check file was created
        assert output_path.exists()
        assert output_path.name == "MODIFIED2025.md"
        
        # Check content
        content = output_path.read_text()
        assert "# 2025" in content
        assert "## Monthly Indexes" in content
        assert "[[MODIFIED2025_10.md]]" in content
        assert "[[MODIFIED2025_11.md]]" in content
        assert "October:" in content
        assert "November:" in content
        assert "(1 text, 1 media files)" in content
        assert "(1 text, 0 media files)" in content

if __name__ == "__main__":
    test_collect_files_creation_modification()
    test_generate_monthly_index_with_prefix()
    test_generate_yearly_index_with_prefix()
    print("All tests passed!")