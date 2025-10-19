"""
Comprehensive tests for link updating scenarios during file deduplication in the Obsidian vault merger.

This test file covers all possible combinations of:
- Referring file location (root directory vs. subdirectory)
- Referenced file location (root directory vs. subdirectory)
- Referenced file type (media files like images vs. non-media files)
- Deduplicated file destination (in !res directory or another location)

For each scenario, both wiki links [[file]] and markdown links [text](file) are tested.
"""

from pathlib import Path
import pytest
import tempfile
import shutil

from obsidian_bracelet.planner import build_plan
from obsidian_bracelet.apply import apply_plan


class TestLinkUpdating:
    """Test class for link updating scenarios during file deduplication."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def create_vault(self, vault_path: Path, files: dict):
        """Helper to create a vault with specified files and content."""
        vault_path.mkdir(parents=True, exist_ok=True)
        (vault_path / ".obsidian").mkdir(exist_ok=True)
        (vault_path / ".obsidian" / "app.json").write_text("{}")
        
        for file_path, content in files.items():
            full_path = vault_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
    
    def test_link_from_root_to_root_image_deduplicated(self, temp_dir):
        """Test: Referring file in root, referenced image in root, deduplicated to !res."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note referencing an image
        self.create_vault(v1, {
            "note.md": "# Note\n\nSee this image: [[image.png]]\n\nAnd this one: [Alt text](image.png)",
            "image.png": "fake image content 1"
        })
        
        # Create vault2 with the same image (same content)
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "image.png": "fake image content 1"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "image.png").exists()
        
        # Verify the note has updated links
        note_content = (target / "note.md").read_text()
        assert "[[!res/image.png]]" in note_content
        assert "[Alt text](!res/image.png)" in note_content
    
    def test_link_from_subdir_to_root_image_deduplicated(self, temp_dir):
        """Test: Referring file in subdirectory, referenced image in root, deduplicated to !res."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note in subdirectory referencing an image in root
        self.create_vault(v1, {
            "docs/note.md": "# Note\n\nSee this image: [[image.png]]\n\nAnd this one: [Alt text](image.png)",
            "image.png": "fake image content 1"
        })
        
        # Create vault2 with the same image (same content)
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "image.png": "fake image content 1"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "image.png").exists()
        
        # Verify the note has updated links
        note_content = (target / "docs" / "note.md").read_text()
        assert "[[!res/image.png]]" in note_content
        assert "[Alt text](!res/image.png)" in note_content
    
    def test_link_from_root_to_subdir_image_deduplicated(self, temp_dir):
        """Test: Referring file in root, referenced image in subdirectory, deduplicated to !res."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note in root referencing an image in subdirectory
        self.create_vault(v1, {
            "note.md": "# Note\n\nSee this image: [[images/image.png]]\n\nAnd this one: [Alt text](images/image.png)",
            "images/image.png": "fake image content 1"
        })
        
        # Create vault2 with the same image (same content)
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "images/image.png": "fake image content 1"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "images" / "image.png").exists()
        
        # Verify the note has updated links
        note_content = (target / "note.md").read_text()
        assert "[[!res/image.png]]" in note_content
        assert "[Alt text](!res/image.png)" in note_content
    
    def test_link_from_subdir_to_subdir_image_deduplicated(self, temp_dir):
        """Test: Referring file in subdirectory, referenced image in another subdirectory, deduplicated to !res."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note in docs referencing an image in assets
        self.create_vault(v1, {
            "docs/note.md": "# Note\n\nSee this image: [[assets/image.png]]\n\nAnd this one: [Alt text](assets/image.png)",
            "assets/image.png": "fake image content 1"
        })
        
        # Create vault2 with the same image (same content)
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "assets/image.png": "fake image content 1"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "assets" / "image.png").exists()
        
        # Verify the note has updated links
        note_content = (target / "docs" / "note.md").read_text()
        assert "[[!res/image.png]]" in note_content
        assert "[Alt text](!res/image.png)" in note_content
    
    def test_link_from_root_to_root_markdown_deduplicated(self, temp_dir):
        """Test: Referring file in root, referenced markdown in root, deduplicated."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note referencing another markdown file
        self.create_vault(v1, {
            "note.md": "# Note\n\nSee [[referenced.md]]\n\nAnd [this one](referenced.md)",
            "referenced.md": "# Referenced\n\nContent here"
        })
        
        # Create vault2 with the same markdown file (same content)
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "referenced.md": "# Referenced\n\nContent here"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the referenced file exists
        assert (target / "referenced.md").exists()
        
        # Verify the note still has correct links (markdown files don't get !res prefix)
        note_content = (target / "note.md").read_text()
        assert "[[referenced.md]]" in note_content
        assert "[this one](referenced.md)" in note_content
    
    def test_link_from_subdir_to_root_markdown_deduplicated(self, temp_dir):
        """Test: Referring file in subdirectory, referenced markdown in root, deduplicated."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note in subdirectory referencing a markdown in root
        self.create_vault(v1, {
            "docs/note.md": "# Note\n\nSee [[../referenced.md]]\n\nAnd [this one](../referenced.md)",
            "referenced.md": "# Referenced\n\nContent here"
        })
        
        # Create vault2 with the same markdown file (same content)
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "referenced.md": "# Referenced\n\nContent here"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the referenced file exists
        assert (target / "referenced.md").exists()
        
        # Verify the note has correct relative path links
        note_content = (target / "docs" / "note.md").read_text()
        assert "[[../referenced.md]]" in note_content
        assert "[this one](../referenced.md)" in note_content
    
    def test_link_from_root_to_subdir_markdown_deduplicated(self, temp_dir):
        """Test: Referring file in root, referenced markdown in subdirectory, deduplicated."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note in root referencing a markdown in subdirectory
        self.create_vault(v1, {
            "note.md": "# Note\n\nSee [[docs/referenced.md]]\n\nAnd [this one](docs/referenced.md)",
            "docs/referenced.md": "# Referenced\n\nContent here"
        })
        
        # Create vault2 with the same markdown file (same content)
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "docs/referenced.md": "# Referenced\n\nContent here"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the referenced file exists
        assert (target / "docs" / "referenced.md").exists()
        
        # Verify the note has correct relative path links
        note_content = (target / "note.md").read_text()
        assert "[[docs/referenced.md]]" in note_content
        assert "[this one](docs/referenced.md)" in note_content
    
    def test_link_from_subdir_to_subdir_markdown_deduplicated(self, temp_dir):
        """Test: Referring file in subdirectory, referenced markdown in another subdirectory, deduplicated."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note in docs referencing a markdown in assets
        self.create_vault(v1, {
            "docs/note.md": "# Note\n\nSee [[../assets/referenced.md]]\n\nAnd [this one](../assets/referenced.md)",
            "assets/referenced.md": "# Referenced\n\nContent here"
        })
        
        # Create vault2 with the same markdown file (same content)
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "assets/referenced.md": "# Referenced\n\nContent here"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the referenced file exists
        assert (target / "assets" / "referenced.md").exists()
        
        # Verify the note has correct relative path links
        note_content = (target / "docs" / "note.md").read_text()
        assert "[[../assets/referenced.md]]" in note_content
        assert "[this one](../assets/referenced.md)" in note_content
    
    def test_link_update_with_different_names_same_content(self, temp_dir):
        """Test: Link updating when files with different names have same content and get deduplicated."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note referencing an image
        self.create_vault(v1, {
            "note.md": "# Note\n\nSee this image: [[image1.png]]\n\nAnd this one: [Alt text](image1.png)",
            "image1.png": "fake image content"
        })
        
        # Create vault2 with the same image but different name
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "image2.png": "fake image content"  # Same content as image1.png
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify only one image exists (deduplicated)
        assert (target / "!res" / "image1.png").exists()
        assert not (target / "!res" / "image2.png").exists()
        
        # Verify the note has updated links
        note_content = (target / "note.md").read_text()
        assert "[[!res/image1.png]]" in note_content
        assert "[Alt text](!res/image1.png)" in note_content
    
    def test_link_update_with_nested_paths(self, temp_dir):
        """Test: Link updating with deeply nested paths."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with deeply nested structure
        self.create_vault(v1, {
            "level1/level2/level3/note.md": "# Note\n\nSee this image: [[../../assets/image.png]]\n\nAnd [this one](../../assets/image.png)",
            "assets/image.png": "fake image content"
        })
        
        # Create vault2 with the same image
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "assets/image.png": "fake image content"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "assets" / "image.png").exists()
        
        # Verify the note has updated links
        note_content = (target / "level1" / "level2" / "level3" / "note.md").read_text()
        assert "[[!res/image.png]]" in note_content
        assert "[this one](!res/image.png)" in note_content
    
    def test_media_files_same_name_different_paths(self, temp_dir):
        """Test: Media files with the same name in different paths should not overwrite each other."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note referencing an image in assets
        self.create_vault(v1, {
            "note.md": "# Note\n\nSee this image: [[assets/image.png]]\n\nAnd this one: [Alt text](assets/image.png)",
            "assets/image.png": "fake image content from vault1 assets"
        })
        
        # Create vault2 with the same image name but in a different path
        self.create_vault(v2, {
            "other.md": "# Other\n\nSee this image: [[images/image.png]]\n\nAnd this one: [Alt text](images/image.png)",
            "images/image.png": "fake image content from vault2 images"
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify both images exist in their respective paths under !res
        assert (target / "!res" / "assets" / "image.png").exists()
        assert (target / "!res" / "images" / "image.png").exists()
        
        # Verify the content is different
        assets_content = (target / "!res" / "assets" / "image.png").read_text()
        images_content = (target / "!res" / "images" / "image.png").read_text()
        assert assets_content != images_content
        assert "vault1 assets" in assets_content
        assert "vault2 images" in images_content
        
        # Verify the note has updated links
        note_content = (target / "note.md").read_text()
        assert "[[!res/image.png]]" in note_content
        assert "[Alt text](!res/image.png)" in note_content
        
        # Verify the other note has updated links
        other_content = (target / "other.md").read_text()
        assert "[[!res/image.png]]" in other_content
        assert "[Alt text](!res/image.png)" in other_content
    
    def test_markdown_files_same_name_different_paths(self, temp_dir):
        """Test: Markdown files with the same name in different paths should not overwrite each other."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note referencing another markdown in docs
        self.create_vault(v1, {
            "note.md": "# Note\n\nSee [[docs/referenced.md]]\n\nAnd [this one](docs/referenced.md)",
            "docs/referenced.md": "# Referenced from vault1\n\nContent from vault1 docs"
        })
        
        # Create vault2 with the same markdown name but in a different path
        self.create_vault(v2, {
            "other.md": "# Other\n\nSee [[pages/referenced.md]]\n\nAnd [this one](pages/referenced.md)",
            "pages/referenced.md": "# Referenced from vault2\n\nContent from vault2 pages"
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify both markdown files exist in their respective paths
        assert (target / "docs" / "referenced.md").exists()
        assert (target / "pages" / "referenced.md").exists()
        
        # Verify the content is different
        docs_content = (target / "docs" / "referenced.md").read_text()
        pages_content = (target / "pages" / "referenced.md").read_text()
        assert docs_content != pages_content
        assert "vault1 docs" in docs_content
        assert "vault2 pages" in pages_content
        
        # Verify the note has correct links
        note_content = (target / "note.md").read_text()
        assert "[[docs/referenced.md]]" in note_content
        assert "[this one](docs/referenced.md)" in note_content
        
        # Verify the other note has correct links
        other_content = (target / "other.md").read_text()
        assert "[[pages/referenced.md]]" in other_content
        assert "[this one](pages/referenced.md)" in other_content
    
    def test_link_update_mixed_scenarios(self, temp_dir):
        """Test: Multiple link updating scenarios in a single vault."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with various link types
        self.create_vault(v1, {
            "root_note.md": "# Root Note\n\nSee [[image.png]] and [[doc.md]]\n\nAnd [image](image.png) and [doc](doc.md)",
            "subdir/note.md": "# Subdir Note\n\nSee [[../image.png]] and [[../doc.md]]\n\nAnd [image](../image.png) and [doc](../doc.md)",
            "image.png": "fake image content",
            "doc.md": "# Document\n\nContent"
        })
        
        # Create vault2 with the same files
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "image.png": "fake image content",  # Same content
            "doc.md": "# Document\n\nContent"   # Same content
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify files exist in correct locations
        assert (target / "!res" / "image.png").exists()
        assert (target / "doc.md").exists()
        
        # Verify root note has updated links
        root_note = (target / "root_note.md").read_text()
        assert "[[!res/image.png]]" in root_note
        assert "[[doc.md]]" in root_note
        assert "[image](!res/image.png)" in root_note
        assert "[doc](doc.md)" in root_note
        
        # Verify subdir note has updated links
        subdir_note = (target / "subdir" / "note.md").read_text()
        assert "[[!res/image.png]]" in subdir_note
        assert "[[../doc.md]]" in subdir_note
        assert "[image](!res/image.png)" in subdir_note
        assert "[doc](../doc.md)" in subdir_note
    
    def test_no_unnecessary_upward_navigation(self, temp_dir):
        """Test the specific issue: links shouldn't have unnecessary '../' components."""
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create vault1 with a note in subdirectory referencing an image
        self.create_vault(v1, {
            "docs/note.md": "# Note\n\nSee this image: [[assets/img.png]]\n\nAnd this one: [Alt text](assets/img.png)",
            "assets/img.png": "fake image content"
        })
        
        # Create vault2 with the same image
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "assets/img.png": "fake image content"  # Same content as in vault1
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "assets" / "img.png").exists()
        
        # Verify the note has updated links WITHOUT unnecessary '../'
        note_content = (target / "docs" / "note.md").read_text()
        
        # The links should point directly to !res/img.png (no directory structure preserved)
        # NOT through ../!res/assets/img.png
        assert "[[!res/img.png]]" in note_content
        assert "[Alt text](!res/img.png)" in note_content
        
        # Verify we don't have incorrect paths with unnecessary '../'
        assert "../!res/assets/img.png" not in note_content
        assert "!res/../assets/img.png" not in note_content
    
    def test_reproduce_unnecessary_upward_navigation_issue(self, temp_dir):
        """
        Test to reproduce the specific issue reported by the user:
        Links ending up with unnecessary "../" components like `../files/img.png`
        
        This test focuses on the scenario where a referring file in a subdirectory
        references a media file that gets deduplicated and moved to the !res directory.
        """
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create a deeply nested structure that might trigger the issue
        self.create_vault(v1, {
            "level1/level2/level3/docs/note.md": """# Deeply Nested Note

This note is in a deeply nested structure and references an image.

Wiki link: [[../../../files/img.png]]

Markdown link: [Image](../../../files/img.png)

Another wiki link: [[files/img.png]]

Another markdown link: [Image](files/img.png)
""",
            "files/img.png": "fake image content from deeply nested structure"
        })
        
        # Create vault2 with the same image but in a different location
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "files/img.png": "fake image content from deeply nested structure"  # Same content
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "files" / "img.png").exists()
        
        # Check the content of the note
        note_content = (target / "level1" / "level2" / "level3" / "docs" / "note.md").read_text()
        
        # Print the content for debugging
        print("\n=== ACTUAL NOTE CONTENT ===")
        print(note_content)
        print("=== END NOTE CONTENT ===\n")
        
        # Check if we have the issue with unnecessary "../" components
        has_unnecessary_nav = (
            "../!res/files/img.png" in note_content or
            "!res/../files/img.png" in note_content or
            "../../!res/files/img.png" in note_content or
            "../../../!res/files/img.png" in note_content
        )
        
        if has_unnecessary_nav:
            print("ISSUE REPRODUCED: Found unnecessary '../' components in links!")
            # If we found the issue, the test should fail to indicate the problem
            assert False, f"Found unnecessary '../' components in links: {note_content}"
        else:
            print("No unnecessary '../' components found in this test case.")
            
            # Verify the links are correctly updated
            assert "[[!res/img.png]]" in note_content
            assert "[Image](!res/img.png)" in note_content
    
    def test_reproduce_issue_with_complex_relative_paths(self, temp_dir):
        """
        Test to reproduce the issue with complex relative paths that might
        result in unnecessary "../" components.
        """
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create a complex structure with various relative path patterns
        self.create_vault(v1, {
            "docs/projects/project1/note.md": """# Project Note

References to images in different locations:

1. Relative up and down: [[../../../assets/images/project1.png]]
2. Markdown version: [Project Image](../../../assets/images/project1.png)
3. Direct reference: [[assets/images/project1.png]]
4. Markdown direct: [Project Image](assets/images/project1.png)
""",
            "assets/images/project1.png": "fake project1 image content"
        })
        
        # Create vault2 with the same image but in a different location
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "assets/images/project1.png": "fake project1 image content"  # Same content
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "assets" / "images" / "project1.png").exists()
        
        # Check the content of the note
        note_content = (target / "docs" / "projects" / "project1" / "note.md").read_text()
        
        # Print the content for debugging
        print("\n=== ACTUAL NOTE CONTENT ===")
        print(note_content)
        print("=== END NOTE CONTENT ===\n")
        
        # Check if we have the issue with unnecessary "../" components
        has_unnecessary_nav = (
            "../!res/assets/images/project1.png" in note_content or
            "!res/../assets/images/project1.png" in note_content or
            "../../!res/assets/images/project1.png" in note_content or
            "../../../!res/assets/images/project1.png" in note_content
        )
        
        if has_unnecessary_nav:
            print("ISSUE REPRODUCED: Found unnecessary '../' components in links!")
            # If we found the issue, the test should fail to indicate the problem
            assert False, f"Found unnecessary '../' components in links: {note_content}"
        else:
            print("No unnecessary '../' components found in this test case.")
            
            # Verify the links are correctly updated
            assert "[[!res/project1.png]]" in note_content
            assert "[Project Image](!res/project1.png)" in note_content
    
    def test_reproduce_issue_with_wiki_link_aliases(self, temp_dir):
        """
        Test to reproduce the issue with wiki links that have aliases.
        This is a specific issue where the alias is lost during link updating.
        """
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create a structure with wiki links that have aliases
        self.create_vault(v1, {
            "docs/note.md": """# Note with Wiki Link Aliases

Wiki link with alias: [[Image|../files/img.png]]

Another with alias: [[Cool Picture|files/img.png]]

Complex path with alias: [[Photo|../../other/files/img.png]]
""",
            "files/img.png": "fake image content"
        })
        
        # Create vault2 with the same image but in a different location
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "files/img.png": "fake image content"  # Same content
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "files" / "img.png").exists()
        
        # Check the content of the note
        note_content = (target / "docs" / "note.md").read_text()
        
        # Print the content for debugging
        print("\n=== ACTUAL NOTE CONTENT ===")
        print(note_content)
        print("=== END NOTE CONTENT ===\n")
        
        # Check if the aliases are preserved
        alias_preserved = (
            "[[Image|!res/img.png]]" in note_content and
            "[[Cool Picture|!res/img.png]]" in note_content and
            "[[Photo|!res/img.png]]" in note_content
        )
        
        if not alias_preserved:
            print("ISSUE REPRODUCED: Wiki link aliases are not preserved!")
            # If we found the issue, the test should fail to indicate the problem
            assert False, f"Wiki link aliases are not preserved: {note_content}"
        else:
            print("Wiki link aliases are correctly preserved.")
    
    def test_reproduce_issue_with_mixed_link_types(self, temp_dir):
        """
        Test to reproduce the issue with mixed link types and complex paths.
        """
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create a structure with mixed link types
        self.create_vault(v1, {
            "docs/note.md": """# Note with Mixed Links

Wiki link with alias: [[Image|../files/img.png]]

Markdown link: [Image](../files/img.png)

Wiki link without alias: [[../files/img.png]]

Complex path: [[../../other/files/img.png]]

Complex markdown: [Image](../../other/files/img.png)
""",
            "files/img.png": "fake image content"
        })
        
        # Create vault2 with the same image but in a different location
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "files/img.png": "fake image content"  # Same content
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the image is in !res
        assert (target / "!res" / "files" / "img.png").exists()
        
        # Check the content of the note
        note_content = (target / "docs" / "note.md").read_text()
        
        # Print the content for debugging
        print("\n=== ACTUAL NOTE CONTENT ===")
        print(note_content)
        print("=== END NOTE CONTENT ===\n")
        
        # Check if we have the issue with unnecessary "../" components
        has_unnecessary_nav = (
            "../!res/files/img.png" in note_content or
            "!res/../files/img.png" in note_content or
            "../../!res/files/img.png" in note_content or
            "!res/../../files/img.png" in note_content
        )
        
        if has_unnecessary_nav:
            print("ISSUE REPRODUCED: Found unnecessary '../' components in links!")
            # If we found the issue, the test should fail to indicate the problem
            assert False, f"Found unnecessary '../' components in links: {note_content}"
        else:
            print("No unnecessary '../' components found in this test case.")
            
            # Verify the links are correctly updated (but note that aliases are currently not preserved)
            # This test is designed to detect the unnecessary "../" issue, not the alias issue
            assert "[[!res/img.png]]" in note_content
            assert "[Image](!res/img.png)" in note_content
    
    def test_specific_user_reported_issue(self, temp_dir):
        """
        Test to specifically reproduce the exact issue reported by the user:
        Links ending up with unnecessary "../" components like `../files/img.png`
        
        This test creates a scenario that closely matches what the user described.
        """
        v1 = temp_dir / "vault1"
        v2 = temp_dir / "vault2"
        target = temp_dir / "merged"
        
        # Create a scenario that matches the user's report
        self.create_vault(v1, {
            "project/docs/note.md": """# Project Documentation

Here are some images referenced from this note:

1. [[../files/diagram.png]]
2. [Diagram](../files/diagram.png)
3. [[../files/chart.png|Chart]]
4. [Chart](../files/chart.png)

These should be updated to point to !res without unnecessary "../" components.
""",
            "project/files/diagram.png": "fake diagram content",
            "project/files/chart.png": "fake chart content"
        })
        
        # Create vault2 with the same files to trigger deduplication
        self.create_vault(v2, {
            "other.md": "# Other\n\nSome content",
            "files/diagram.png": "fake diagram content",  # Same content
            "files/chart.png": "fake chart content"       # Same content
        })
        
        # Build and apply plan
        plan = build_plan([v1, v2], target)
        apply_plan(plan)
        
        # Verify the images are in !res
        assert (target / "!res" / "files" / "diagram.png").exists()
        assert (target / "!res" / "files" / "chart.png").exists()
        
        # Check the content of the note
        note_content = (target / "project" / "docs" / "note.md").read_text()
        
        # Print the content for debugging
        print("\n=== ACTUAL NOTE CONTENT ===")
        print(note_content)
        print("=== END NOTE CONTENT ===\n")
        
        # Check for the specific issue: links with unnecessary "../" components
        problematic_patterns = [
            "../!res/files/diagram.png",
            "!res/../files/diagram.png",
            "../!res/files/chart.png",
            "!res/../files/chart.png"
        ]
        
        found_issue = False
        for pattern in problematic_patterns:
            if pattern in note_content:
                print(f"ISSUE REPRODUCED: Found problematic pattern: {pattern}")
                found_issue = True
        
        if found_issue:
            assert False, f"Found unnecessary '../' components in links: {note_content}"
        else:
            print("SUCCESS: No unnecessary '../' components found.")
            
            # Verify the links are correctly updated
            assert "[[!res/diagram.png]]" in note_content
            assert "[Diagram](!res/diagram.png)" in note_content
            assert "[[Chart|!res/chart.png]]" in note_content
            assert "[Chart](!res/chart.png)" in note_content