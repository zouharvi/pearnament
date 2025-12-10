"""Tests for campaign data validation."""

import json
import os
import tempfile

import pytest


class TestItemValidation:
    """Tests for item structure validation."""

    def test_valid_task_based(self):
        """Test that valid task-based campaign passes validation."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_valid",
                    "info": {
                        "assignment": "task-based",
                    },
                    "data": [
                        [
                            [
                                {"src": "hello", "tgt": {"model_A": "hola", "model_B": "ola"}},
                                {"src": "world", "tgt": {"model_A": "mundo", "model_B": "munda"}}
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
                        "users": 2,
                    },
                    "data": [
                        [
                            {"src": "hello", "tgt": {"model_A": "hola"}},
                            {"src": "world", "tgt": {"model_A": "mundo"}}
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
                    },
                    "data": [
                        [
                            [
                                {"tgt": {"model_A": "hola"}}  # Missing 'src'
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
                    },
                    "data": [
                        [
                            {"src": "hello", "tgt": {"model_A": "hola"}}  # Should be list of items
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
                        "users": 2,
                    },
                    "data": [
                        [
                            {"tgt": {"model_A": "hola"}}  # Missing 'src'
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
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "hello",
                                    "tgt": {"model_A": "hola"},
                                    "doc_id": "123",
                                    "instructions": "Translate this",
                                    "validation": {"model_A": {"score": [70, 80]}}
                                }
                            ]
                        ]
                    ]
                }, f)

            # Should not raise - extra keys are fine, use overwrite to avoid conflicts
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_src_must_be_string(self):
        """Test that src must be a string."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_src_not_string",
                    "info": {
                        "assignment": "task-based",
                    },
                    "data": [
                        [
                            [
                                {"src": 123, "tgt": {"model_A": "hello"}}  # src is not a string
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="'src' must be a string"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_tgt_must_be_dict(self):
        """Test that tgt must be a dict."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_tgt_not_dict",
                    "info": {
                        "assignment": "task-based",
                    },
                    "data": [
                        [
                            [
                                {"src": "hello", "tgt": "not a dict"}
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="'tgt' must be a dictionary"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_tgt_dict_number_only_name_fails(self):
        """Test that number-only model names are rejected."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_number_only",
                    "info": {
                        "assignment": "task-based",
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "hello",
                                    "tgt": {
                                        "1": "hola",
                                        "2": "ola"
                                    }
                                }
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="cannot be number-only"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_shuffle_default_true(self):
        """Test that shuffle defaults to true."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_shuffle_default",
                    "info": {
                        "assignment": "task-based",
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "hello",
                                    "tgt": {
                                        "model_A": "hola",
                                        "model_B": "ola",
                                        "model_C": "salut"
                                    }
                                }
                            ]
                        ]
                    ]
                }, f)

            # Should not raise and should shuffle by default
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_shuffle_false(self):
        """Test that shuffle can be disabled."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_no_shuffle",
                    "info": {
                        "assignment": "task-based",
                        "shuffle": False,
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "hello",
                                    "tgt": {
                                        "model_A": "hola",
                                        "model_B": "ola",
                                        "model_C": "salut"
                                    }
                                }
                            ]
                        ]
                    ]
                }, f)

            # Should not raise
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_shuffle_must_be_bool(self):
        """Test that shuffle parameter must be a boolean."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_shuffle_not_bool",
                    "info": {
                        "assignment": "task-based",
                        "shuffle": "yes",  # Should be bool
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "hello",
                                    "tgt": {
                                        "model_A": "hola",
                                        "model_B": "ola"
                                    }
                                }
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="must be a boolean"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_template_optional(self):
        """Test that template parameter is optional."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_no_template",
                    "info": {
                        "assignment": "task-based",
                        # No template specified - should default to 'basic'
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "hello",
                                    "tgt": {"model_A": "hola"}
                                }
                            ]
                        ]
                    ]
                }, f)

            # Should not raise
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_score_greaterthan_with_dict(self):
        """Test that score_greaterthan validation works with dict format."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_score_greaterthan",
                    "info": {
                        "assignment": "task-based",
                        "protocol": "DA",
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "AI transforms industries.",
                                    "tgt": {
                                        "model_A": "UI transformuje průmysly.",
                                        "model_B": "Umělá inteligence mění obory."
                                    },
                                    "validation": {
                                        "model_A": {
                                            "warning": "A has error, score 20-40.",
                                            "score": [20, 40]
                                        },
                                        "model_B": {
                                            "warning": "B is correct and must score higher than A.",
                                            "score": [70, 90],
                                            "score_greaterthan": "model_A"
                                        }
                                    }
                                }
                            ]
                        ]
                    ]
                }, f)

            # Should not raise - score_greaterthan validation should work with dict format
            _add_single_campaign(campaign_file, True, "http://localhost:8001")
