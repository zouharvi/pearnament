"""Tests for CLI functionality."""

import json
import os
import random
import tempfile

import pytest


class TestAssetsValidation:
    """Tests for assets validation in add command."""

    def test_assets_must_be_dict(self):
        """Test that assets must be a dictionary."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test assets directory
            assets_dir = os.path.join(tmpdir, "videos")
            os.makedirs(assets_dir)

            # Create campaign with string assets (old format)
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_campaign",
                    "info": {
                        "assignment": "task-based",
                        "template": "basic",
                        "assets": assets_dir,
                    },
                    "data": [[[{"src": "a", "tgt": {"A": "b"}}]]]
                }, f)

            with pytest.raises(ValueError, match="Assets must be a dictionary"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_assets_requires_source_key(self):
        """Test that assets must have source key."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_campaign",
                    "info": {
                        "assignment": "task-based",
                        "template": "basic",
                        "assets": {"destination": "assets/my_videos"},
                    },
                    "data": [[[{"src": "a", "tgt": {"A": "b"}}]]]
                }, f)

            with pytest.raises(ValueError, match="must contain 'source' and 'destination' keys"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_assets_requires_destination_key(self):
        """Test that assets must have destination key."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = os.path.join(tmpdir, "videos")
            os.makedirs(assets_dir)

            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_campaign",
                    "info": {
                        "assignment": "task-based",
                        "template": "basic",
                        "assets": {"source": assets_dir},
                    },
                    "data": [[[{"src": "a", "tgt": {"A": "b"}}]]]
                }, f)

            with pytest.raises(ValueError, match="must contain 'source' and 'destination' keys"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_assets_destination_must_start_with_assets(self):
        """Test that assets destination must start with 'assets/'."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            assets_dir = os.path.join(tmpdir, "videos")
            os.makedirs(assets_dir)

            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_campaign",
                    "info": {
                        "assignment": "task-based",
                        "template": "basic",
                        "assets": {
                            "source": assets_dir,
                            "destination": "my_videos"
                        },
                    },
                    "data": [[[{"src": "a", "tgt": {"A": "b"}}]]]
                }, f)

            with pytest.raises(ValueError, match="must start with 'assets/'"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_assets_source_must_exist(self):
        """Test that assets source directory must exist."""
        from pearmut.cli import ROOT, STATIC_DIR, _add_single_campaign

        # Create static directory for this test
        os.makedirs(f"{STATIC_DIR}/assets", exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create data directory
            data_dir = f"{ROOT}/data/tasks"
            os.makedirs(data_dir, exist_ok=True)

            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_campaign",
                    "info": {
                        "assignment": "task-based",
                        "template": "basic",
                        "assets": {
                            "source": "/nonexistent/path",
                            "destination": "assets/my_videos"
                        },
                    },
                    "data": [[[{"src": "a", "tgt": {"A": "b"}}]]]
                }, f)

            with pytest.raises(ValueError, match="must be an existing directory"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")


class TestShuffleData:
    """Tests for shuffle functionality in campaigns."""

    def test_shuffle_reorders_models(self):
        """Test that shuffle reorders model names in tgt dictionary."""
        from pearmut.cli import _shuffle_campaign_data
        
        rng = random.Random(42)
        campaign_data = {
            "info": {"assignment": "task-based"},
            "data": {
                "user1": [
                    [  # Document 1
                        {"src": "hello", "tgt": {"model_A": "hola", "model_B": "bonjour", "model_C": "ciao"}},
                        {"src": "world", "tgt": {"model_A": "mundo", "model_B": "monde", "model_C": "mondo"}}
                    ]
                ]
            }
        }
        
        # Get original order
        original_order = list(campaign_data["data"]["user1"][0][0]["tgt"].keys())
        
        # Shuffle
        _shuffle_campaign_data(campaign_data, rng)
        
        # Get new order
        new_order = list(campaign_data["data"]["user1"][0][0]["tgt"].keys())
        
        # Order should be different (with seed 42 and 3 models, it will be shuffled)
        assert new_order != original_order
        
        # All models should still be present
        assert set(new_order) == set(original_order)
        
        # Both items in the document should have the same order
        doc = campaign_data["data"]["user1"][0]
        assert list(doc[0]["tgt"].keys()) == list(doc[1]["tgt"].keys())
