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
                                    "model": "system1",
                                    "instructions": "Translate this",
                                    "validation": {"score": [70, 80]}
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
                        "template": "pointwise",
                    },
                    "data": [
                        [
                            [
                                {"src": 123, "tgt": "hello"}  # src is not a string
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="'src' must be a string"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_pointwise_tgt_must_be_string(self):
        """Test that tgt must be a string for pointwise template."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_pointwise_tgt_not_string",
                    "info": {
                        "assignment": "task-based",
                        "template": "pointwise",
                    },
                    "data": [
                        [
                            [
                                {"src": "hello", "tgt": ["list", "not", "string"]}
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="'tgt' must be a string for pointwise template"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_listwise_tgt_must_be_list(self):
        """Test that tgt must be a list for listwise template."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_listwise_tgt_not_list",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
                    },
                    "data": [
                        [
                            [
                                {"src": "hello", "tgt": "not a list"}
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="'tgt' must be a list for listwise template"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_listwise_tgt_elements_must_be_strings(self):
        """Test that all elements in tgt list must be strings for listwise."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_listwise_tgt_non_string_element",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
                    },
                    "data": [
                        [
                            [
                                {"src": "hello", "tgt": ["valid", 123, "another"]}
                            ]
                        ]
                    ]
                }, f)

            with pytest.raises(ValueError, match="All elements in 'tgt' list must be strings"):
                _add_single_campaign(campaign_file, False, "http://localhost:8001")

    def test_listwise_with_score_greaterthan_validation(self):
        """Test that listwise campaigns with score_greaterthan validation can be loaded."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_listwise_score_greaterthan",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
                        "protocol": "DA",
                    },
                    "data": [
                        [
                            [
                                {
                                    "src": "Test source text.",
                                    "tgt": ["Translation A", "Translation B"],
                                    "validation": [
                                        {
                                            "warning": "A must score higher than B.",
                                            "score": [80, 100],
                                            "score_greaterthan": 1
                                        },
                                        {
                                            "warning": "B should score lower.",
                                            "score": [40, 70]
                                        }
                                    ]
                                }
                            ]
                        ]
                    ]
                }, f)

            # Should not raise - the score_greaterthan field is valid
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_listwise_tgt_dict_valid(self):
        """Test that listwise campaigns with dict tgt are valid."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_listwise_dict",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
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

            # Should not raise
            _add_single_campaign(campaign_file, True, "http://localhost:8001")

    def test_listwise_tgt_dict_number_only_name_fails(self):
        """Test that number-only model names are rejected."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_listwise_number_only",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
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

    def test_listwise_shuffle_default_true(self):
        """Test that shuffle defaults to true for listwise."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_listwise_shuffle_default",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
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

    def test_listwise_shuffle_false(self):
        """Test that shuffle can be disabled."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_listwise_no_shuffle",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
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

    def test_listwise_shuffle_must_be_bool(self):
        """Test that shuffle parameter must be a boolean."""
        from pearmut.cli import _add_single_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_file = os.path.join(tmpdir, "campaign.json")
            with open(campaign_file, "w") as f:
                json.dump({
                    "campaign_id": "test_listwise_shuffle_not_bool",
                    "info": {
                        "assignment": "task-based",
                        "template": "listwise",
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
