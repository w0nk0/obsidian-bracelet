import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_bracelet.planner import build_plan
from obsidian_bracelet.apply import apply_plan

def test_non_text_file_deduplication():
    """Test that duplicate non-text files are not replaced with markdown links."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create two source vaults with identical non-text files
        vault1 = tmpdir / "vault1"
        vault2 = tmpdir / "vault2"
        target = tmpdir / "target"
        
        vault1.mkdir()
        vault2.mkdir()
        
        # Create .obsidian directories to make them valid vaults
        (vault1 / ".obsidian").mkdir()
        (vault2 / ".obsidian").mkdir()
        
        # Create identical binary files in both vaults
        binary_content = b"binary data content here"
        (vault1 / "data.bin").write_bytes(binary_content)
        (vault2 / "data.bin").write_bytes(binary_content)
        
        # Create identical image files in both vaults
        image_content = b"fake image data"
        (vault1 / "image.png").write_bytes(image_content)
        (vault2 / "image.png").write_bytes(image_content)
        
        # Create identical text files for comparison
        text_content = "# Test File\n\nThis is a test file."
        (vault1 / "test.md").write_text(text_content)
        (vault2 / "test.md").write_text(text_content)
        
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
        
        # We should have one copy action for the binary file (in !res)
        bin_copies = [a for a in copy_actions if "data.bin" in a["dest"]]
        print(f"Binary copies: {len(bin_copies)}")
        
        # We should have one copy action for the image file (in !res)
        img_copies = [a for a in copy_actions if "image.png" in a["dest"]]
        print(f"Image copies: {len(img_copies)}")
        
        # We should have one copy action for the text file
        text_copies = [a for a in copy_actions if "test.md" in a["dest"]]
        print(f"Text copies: {len(text_copies)}")
        
        # For text files, we should have a link file
        text_links = [a for a in link_actions if "test.md" in a["dest"]]
        print(f"Text links: {len(text_links)}")
        
        # For non-text files, we should NOT have link files
        bin_links = [a for a in link_actions if "data.bin" in a["dest"]]
        print(f"Binary links: {len(bin_links)}")
        
        img_links = [a for a in link_actions if "image.png" in a["dest"]]
        print(f"Image links: {len(img_links)}")
        
        # Check notes for proper deduplication messages
        non_text_notes = [n for n in plan["notes"] if "non-text file" in n]
        print(f"Non-text notes: {len(non_text_notes)}")
        
        # Apply the plan
        apply_plan(plan)
        
        # Check that files exist in target
        assert (target / "!res" / "data.bin").exists()
        assert (target / "!res" / "image.png").exists()
        assert (target / "test.md").exists()
        
        # Verify content is correct
        assert (target / "!res" / "data.bin").read_bytes() == binary_content
        assert (target / "!res" / "image.png").read_bytes() == image_content
        assert (target / "test.md").read_text() == text_content
        
        print("\nTest passed: Non-text files are properly deduplicated without creating markdown link files")

if __name__ == "__main__":
    test_non_text_file_deduplication()