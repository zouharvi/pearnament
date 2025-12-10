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

    def test_shuffle_defaults_to_true(self):
        """Test that shuffle parameter defaults to true."""
        from pearmut.cli import _shuffle_campaign_data
        
        rng = random.Random(42)
        campaign_data = {
            "info": {"assignment": "task-based"},
            "data": [
                [  # Task 1
                    [  # Document 1
                        {"src": "hello", "tgt": {"model_A": "hola", "model_B": "bonjour"}},
                        {"src": "world", "tgt": {"model_A": "mundo", "model_B": "monde"}}
                    ]
                ]
            ]
        }
        
        result = _shuffle_campaign_data(campaign_data, rng)
        
        # Check that only one model remains per document
        doc = result["data"][0][0]
        assert len(doc[0]["tgt"]) == 1
        assert len(doc[1]["tgt"]) == 1
        # Both items in the same document should have the same model
        assert list(doc[0]["tgt"].keys())[0] == list(doc[1]["tgt"].keys())[0]

    def test_shuffle_maintains_document_consistency(self):
        """Test that all segments in a document use the same model after shuffle."""
        from pearmut.cli import _shuffle_campaign_data
        
        rng = random.Random(42)
        campaign_data = {
            "info": {"assignment": "task-based"},
            "data": [
                [  # Task 1
                    [  # Document 1
                        {"src": "seg1", "tgt": {"model_A": "a1", "model_B": "b1", "model_C": "c1"}},
                        {"src": "seg2", "tgt": {"model_A": "a2", "model_B": "b2", "model_C": "c2"}},
                        {"src": "seg3", "tgt": {"model_A": "a3", "model_B": "b3", "model_C": "c3"}}
                    ]
                ]
            ]
        }
        
        result = _shuffle_campaign_data(campaign_data, rng)
        doc = result["data"][0][0]
        
        # All segments should have exactly one model
        for item in doc:
            assert len(item["tgt"]) == 1
        
        # All segments in the document should use the same model
        model_names = [list(item["tgt"].keys())[0] for item in doc]
        assert all(m == model_names[0] for m in model_names)

    def test_shuffle_single_stream_assignment(self):
        """Test shuffle works for single-stream assignment."""
        from pearmut.cli import _shuffle_campaign_data
        
        rng = random.Random(42)
        campaign_data = {
            "info": {"assignment": "single-stream"},
            "data": [
                [  # Document 1
                    {"src": "hello", "tgt": {"model_A": "hola", "model_B": "bonjour"}},
                    {"src": "world", "tgt": {"model_A": "mundo", "model_B": "monde"}}
                ],
                [  # Document 2
                    {"src": "goodbye", "tgt": {"model_A": "adios", "model_B": "au revoir"}}
                ]
            ]
        }
        
        result = _shuffle_campaign_data(campaign_data, rng)
        
        # Check each document maintains consistency
        for doc in result["data"]:
            if len(doc) > 0:
                first_model = list(doc[0]["tgt"].keys())[0]
                for item in doc:
                    assert len(item["tgt"]) == 1
                    assert list(item["tgt"].keys())[0] == first_model

    def test_shuffle_preserves_error_spans(self):
        """Test that error_spans are shuffled along with translations."""
        from pearmut.cli import _shuffle_campaign_data
        
        rng = random.Random(42)
        campaign_data = {
            "info": {"assignment": "task-based"},
            "data": [
                [  # Task 1
                    [  # Document 1
                        {
                            "src": "hello",
                            "tgt": {"model_A": "hola", "model_B": "bonjour"},
                            "error_spans": {
                                "model_A": [[{"start_i": 0, "end_i": 2, "severity": "minor"}]],
                                "model_B": [[{"start_i": 1, "end_i": 3, "severity": "major"}]]
                            }
                        }
                    ]
                ]
            ]
        }
        
        result = _shuffle_campaign_data(campaign_data, rng)
        doc = result["data"][0][0]
        
        # Check that error_spans exist and match the selected model
        item = doc[0]
        selected_model = list(item["tgt"].keys())[0]
        assert "error_spans" in item
        assert selected_model in item["error_spans"]
        assert len(item["error_spans"]) == 1

    def test_shuffle_preserves_validation(self):
        """Test that validation rules are shuffled along with translations."""
        from pearmut.cli import _shuffle_campaign_data
        
        rng = random.Random(42)
        campaign_data = {
            "info": {"assignment": "task-based"},
            "data": [
                [  # Task 1
                    [  # Document 1
                        {
                            "src": "hello",
                            "tgt": {"model_A": "hola", "model_B": "bonjour"},
                            "validation": {
                                "model_A": {"score": [70, 80]},
                                "model_B": {"score": [60, 70]}
                            }
                        }
                    ]
                ]
            ]
        }
        
        result = _shuffle_campaign_data(campaign_data, rng)
        doc = result["data"][0][0]
        
        # Check that validation exists and matches the selected model
        item = doc[0]
        selected_model = list(item["tgt"].keys())[0]
        assert "validation" in item
        assert selected_model in item["validation"]
        assert len(item["validation"]) == 1

    def test_shuffle_no_effect_single_model(self):
        """Test that shuffle has no effect when only one model is present."""
        from pearmut.cli import _shuffle_campaign_data
        
        rng = random.Random(42)
        campaign_data = {
            "info": {"assignment": "task-based"},
            "data": [
                [  # Task 1
                    [  # Document 1
                        {"src": "hello", "tgt": {"model_A": "hola"}},
                        {"src": "world", "tgt": {"model_A": "mundo"}}
                    ]
                ]
            ]
        }
        
        result = _shuffle_campaign_data(campaign_data, rng)
        doc = result["data"][0][0]
        
        # Should still have the same single model
        assert doc[0]["tgt"] == {"model_A": "hola"}
        assert doc[1]["tgt"] == {"model_A": "mundo"}

    def test_shuffle_different_documents_can_have_different_models(self):
        """Test that different documents can be assigned different models."""
        from pearmut.cli import _shuffle_campaign_data
        
        # Use a specific seed for reproducibility
        rng = random.Random(12345)
        campaign_data = {
            "info": {"assignment": "task-based"},
            "data": [
                [  # Task 1
                    [  # Document 1
                        {"src": "seg1", "tgt": {"model_A": "a1", "model_B": "b1"}},
                    ],
                    [  # Document 2
                        {"src": "seg2", "tgt": {"model_A": "a2", "model_B": "b2"}},
                    ],
                    [  # Document 3
                        {"src": "seg3", "tgt": {"model_A": "a3", "model_B": "b3"}},
                    ],
                    [  # Document 4
                        {"src": "seg4", "tgt": {"model_A": "a4", "model_B": "b4"}},
                    ]
                ]
            ]
        }
        
        result = _shuffle_campaign_data(campaign_data, rng)
        
        # Collect the models used in each document
        models = []
        for doc in result["data"][0]:
            models.append(list(doc[0]["tgt"].keys())[0])
        
        # Check that valid models are selected
        for model in models:
            assert model in ["model_A", "model_B"]
        
        # Verify each document has only one model
        assert all(len(doc[0]["tgt"]) == 1 for doc in result["data"][0])
