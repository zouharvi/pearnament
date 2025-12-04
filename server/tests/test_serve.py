"""Tests for the serve command and meta.json functionality."""

import json
import os
import tempfile

import pytest

from pearmut.utils import ROOT, load_meta_data, save_meta_data


class TestMetaData:
    """Tests for meta.json loading and saving."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Save original meta.json if it exists
        meta_path = f"{ROOT}/data/meta.json"
        self.original_meta = None
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                self.original_meta = f.read()
        
        # Ensure data directory exists
        os.makedirs(f"{ROOT}/data", exist_ok=True)
        
        yield
        
        # Restore original meta.json
        if self.original_meta is not None:
            with open(meta_path, "w") as f:
                f.write(self.original_meta)
        elif os.path.exists(meta_path):
            os.remove(meta_path)

    def test_load_meta_data_creates_default(self):
        """Test that load_meta_data returns default structure when file doesn't exist."""
        meta_path = f"{ROOT}/data/meta.json"
        if os.path.exists(meta_path):
            os.remove(meta_path)
        
        meta = load_meta_data()
        assert meta == {"served_directories": []}

    def test_save_and_load_meta_data(self):
        """Test that save_meta_data and load_meta_data work correctly."""
        test_data = {"served_directories": ["/path/to/dir1", "/path/to/dir2"]}
        save_meta_data(test_data)
        
        loaded = load_meta_data()
        assert loaded == test_data

    def test_load_meta_data_with_existing_file(self):
        """Test that load_meta_data correctly reads existing file."""
        meta_path = f"{ROOT}/data/meta.json"
        test_data = {"served_directories": ["/custom/path"]}
        with open(meta_path, "w") as f:
            json.dump(test_data, f)
        
        loaded = load_meta_data()
        assert loaded == test_data


class TestServeCommand:
    """Tests for the serve command functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Save original meta.json if it exists
        meta_path = f"{ROOT}/data/meta.json"
        self.original_meta = None
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                self.original_meta = f.read()
        
        # Ensure data directory exists
        os.makedirs(f"{ROOT}/data", exist_ok=True)
        
        # Create a temp directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        yield
        
        # Restore original meta.json
        if self.original_meta is not None:
            with open(meta_path, "w") as f:
                f.write(self.original_meta)
        elif os.path.exists(meta_path):
            os.remove(meta_path)
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_serve_adds_directory(self):
        """Test that serve command adds a directory to meta.json."""
        # Clear meta.json first
        save_meta_data({"served_directories": []})
        
        # Simulate what the serve command does
        meta_data = load_meta_data()
        meta_data["served_directories"].append(self.temp_dir)
        save_meta_data(meta_data)
        
        # Verify
        loaded = load_meta_data()
        assert self.temp_dir in loaded["served_directories"]

    def test_serve_prevents_duplicates(self):
        """Test that serve command prevents duplicate directories."""
        save_meta_data({"served_directories": [self.temp_dir]})
        
        meta_data = load_meta_data()
        if self.temp_dir not in meta_data["served_directories"]:
            meta_data["served_directories"].append(self.temp_dir)
        save_meta_data(meta_data)
        
        loaded = load_meta_data()
        assert loaded["served_directories"].count(self.temp_dir) == 1
