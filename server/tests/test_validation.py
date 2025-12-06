"""Tests for campaign data validation."""

import json
import os
import tempfile

import pytest


class TestItemValidation:
    """Tests for item structure validation."""

    def test_valid_pointwise_task_based(self):
        """Test that valid pointwise task-based campaign passes validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_valid",
                    "info": {
                        "assignment": "task-based",
                        "template": "pointwise",
                    },
                    "data": [
                        [
                            [
                                {"src": "hello", "tgt": "hola"},
                                {"src": "world", "tgt": "mundo"}
                            ]
                        ]
                    ]
                }, f)

            # Should not raise - use overwrite to avoid conflicts
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_valid_listwise_task_based(self):
        """Test that valid listwise task-based campaign passes validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_valid_listwise",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
                    },
                    "data": [
                        [
                            [
                                {"src": "hello", "tgt": ["hola", "ola"]},
                                {"src": "world", "tgt": ["mundo", "munda"]}
                            ]
                        ]
                    ]
                }, f)

            # Should not raise - use overwrite to avoid conflicts
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_valid_singlestream(self):
        """Test that valid single-stream campaign passes validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_valid_ss",
                    "info": {
                        "assignment": "single-stream",
                        "template": "pointwise",
                        "users": 2,
                    },
                    "data": [
                        [
                            {"src": "hello", "tgt": "hola"},
                            {"src": "world", "tgt": "mundo"}
                        ]
                    ]
                }, f)

            # Should not raise - use overwrite to avoid conflicts
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_missing_src_key(self):
        """Test that items without 'src' key fail validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_missing_src",
                    "info": {
                        "assignment": "task-based",
                        "template": "pointwise",
                    },
                    "data": [
                        [
                            [
                                {"tgt": "hola"}  # Missing 'src'
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="must contain 'src' and 'tgt' keys"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_missing_tgt_key(self):
        """Test that items without 'tgt' key fail validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_missing_tgt",
                    "info": {
                        "assignment": "task-based",
                        "template": "pointwise",
                    },
                    "data": [
                        [
                            [
                                {"src": "hello"}  # Missing 'tgt'
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="must contain 'src' and 'tgt' keys"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_item_not_dict(self):
        """Test that non-dict items fail validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_not_dict",
                    "info": {
                        "assignment": "task-based",
                        "template": "pointwise",
                    },
                    "data": [
                        [
                            [
                                "not a dict"  # Should be dict
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="must be a dictionary"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_document_not_list(self):
        """Test that non-list documents fail validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_doc_not_list",
                    "info": {
                        "assignment": "task-based",
                        "template": "pointwise",
                    },
                    "data": [
                        [
                            {"src": "hello", "tgt": "hola"}  # Should be list of items
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="Items must be a list"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_singlestream_missing_src(self):
        """Test that single-stream items without 'src' fail validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_ss_missing_src",
                    "info": {
                        "assignment": "single-stream",
                        "template": "pointwise",
                        "users": 2,
                    },
                    "data": [
                        [
                            {"tgt": "hola"}  # Missing 'src'
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="must contain 'src' and 'tgt' keys"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_extra_keys_allowed(self):
        """Test that extra keys beyond src/tgt are allowed."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_extra_keys",
                    "info": {
                        "assignment": "task-based",
                        "template": "pointwise",
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "hello",
                                    "tgt": "hola",
                                    "doc_id": "123",
                                    "sys_id": "system1",
                                    "instructions": "Translate this",
                                    "validation": {"score": [70, 80]}
                                }
                            ]
                        ]
                    ]
                }, f)

            # Should not raise - extra keys are fine, use overwrite to avoid conflicts
            _add_single_campaign(campaign_file, True, "http://localhost:8001")
