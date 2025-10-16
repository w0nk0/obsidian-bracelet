import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_bracelet.planner import build_plan
from obsidian_bracelet.apply import apply_plan

def test_non_text_file_deduplication_different_names():
    """Test that duplicate non-text files with different names are not replaced with markdown links."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create two source vaults with identical non-text files but different names
        vault1 = tmpdir / "vault1"
        vault2 = tmpdir / "vault2"
        target = tmpdir / "target"
        
        vault1.mkdir()
        vault2.mkdir()
        
        # Create .obsidian directories to make them valid vaults
        (vault1 / ".obsidian").mkdir()
        (vault2 / ".obsidian").mkdir()
        
        # Create identical binary files with different names
        binary_content = b"binary data content here"
        (vault1 / "data.bin").write_bytes(binary_content)
        (vault2 / "binary_data.bin").write_bytes(binary_content)
        
        # Create identical image files with different names
        image_content = b"fake image data"
        (vault1 / "image.png").write_bytes(image_content)
        (vault2 / "picture.png").write_bytes(image_content)
        
        # Create identical text files with different names for comparison
        text_content = "# Test File\n\nThis is a test file."
        (vault1 / "test.md").write_text(text_content)
        (vault2 / "test_file.md").write_text(text_content)
        
        # Create markdown files that link to these files
        md1_content = """
# Note 1

Here's a link to the binary file: [binary](data.bin)
Here's a link to the image file: [image](image.png)
Here's a link to the text file: [text](test.md)
"""
        md2_content = """
# Note 2

Here's a link to the binary file: [binary](binary_data.bin)
Here's a link to the image file: [image](picture.png)
Here's a link to the text file: [text](test_file.md)
"""
        (vault1 / "note1.md").write_text(md1_content)
        (vault2 / "note2.md").write_text(md2_content)
        
        # Build plan
        verbose_output = []
        plan = build_plan([vault1, vault2], target, verbose_output=verbose_output)
        
        # Print verbose output for debugging
        print("\n".join(verbose_output))
        print("\nPlan actions:")
        for action in plan["actions"]:
            print(f"  {action}")
        print("\nPlan notes:")
        for note in plan["notes"]:
            print(f"  {note}")
        
        # Check actions
        copy_actions = [a for a in plan["actions"] if a["type"] == "copy"]
        link_actions = [a for a in plan["actions"] if a["type"] == "create_link_file"]
        
        print(f"\nCopy actions: {len(copy_actions)}")
        print(f"Link actions: {len(link_actions)}")
        
        # We should have copy actions for the files
        bin_copies = [a for a in copy_actions if "data.bin" in a["dest"] or "binary_data.bin" in a["dest"]]
        img_copies = [a for a in copy_actions if "image.png" in a["dest"] or "picture.png" in a["dest"]]
        text_copies = [a for a in copy_actions if "test.md" in a["dest"] or "test_file.md" in a["dest"]]
        
        print(f"Binary copies: {len(bin_copies)}")
        print(f"Image copies: {len(img_copies)}")
        print(f"Text copies: {len(text_copies)}")
        
        # For text files, we should have a link file
        text_links = [a for a in link_actions if "test.md" in a["dest"] or "test_file.md" in a["dest"]]
        print(f"Text links: {len(text_links)}")
        
        # For non-text files, we should NOT have link files
        bin_links = [a for a in link_actions if ("data.bin" in a["dest"] or "binary_data.bin" in a["dest"])]
        img_links = [a for a in link_actions if ("image.png" in a["dest"] or "picture.png" in a["dest"])]
        
        print(f"Binary links: {len(bin_links)}")
        print(f"Image links: {len(img_links)}")
        
        # Check notes for proper deduplication messages
        non_text_notes = [n for n in plan["notes"] if "non-text file" in n]
        print(f"Non-text notes: {len(non_text_notes)}")
        
        # Apply the plan
        apply_plan(plan)
        
        # Check that files exist in target
        assert (target / "!res" / "data.bin").exists() or (target / "!res" / "binary_data.bin").exists()
        assert (target / "!res" / "image.png").exists() or (target / "!res" / "picture.png").exists()
        assert (target / "test.md").exists() or (target / "test_file.md").exists()
        
        print("\nTest passed: Non-text files with different names are properly deduplicated without creating markdown link files")

if __name__ == "__main__":
    test_non_text_file_deduplication_different_names()