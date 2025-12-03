"""Tests for protocol functions."""

from pearmut.assignment import (
    get_next_item,
    reset_task,
    update_progress,
)


class TestTaskBased:
    """Tests for task-based assignment."""

    def test_get_next_item_returns_first_incomplete(self):
        """Test that task-based returns the first incomplete item."""
        tasks_data = {
            "campaign1": {
                "info": {
                    "assignment": "task-based",
                    "template": "pointwise",
                },
                "data": {
                    "user1": [
                        [{"src": "a", "tgt": "b"}],
                        [{"src": "c", "tgt": "d"}],
                        [{"src": "e", "tgt": "f"}],
                    ]
                }
            }
        }
        progress_data = {
            "campaign1": {
                "user1": {
                    "progress": [True, False, False],
                    "time": 0,
                    "token_correct": "abc",
                    "token_incorrect": "xyz",
                }
            }
        }
        response = get_next_item("campaign1", "user1",
                                 tasks_data, progress_data)
        assert response.status_code == 200
        content = response.body.decode()
        assert '"item_i":1' in content

    def test_get_next_item_completed_returns_token(self):
        """Test that task-based returns completion token when all items done."""
        tasks_data = {
            "campaign1": {
                "info": {
                    "assignment": "task-based",
                    "template": "pointwise",
                },
                "data": {
                    "user1": [
                        [{"src": "a", "tgt": "b"}],
                    ]
                }
            }
        }
        progress_data = {
            "campaign1": {
                "user1": {
                    "progress": [True],
                    "time": 100,
                    "token_correct": "correct_token",
                    "token_incorrect": "wrong_token",
                }
            }
        }
        response = get_next_item("campaign1", "user1",
                                 tasks_data, progress_data)
        assert response.status_code == 200
        content = response.body.decode()
        assert '"status":"completed"' in content
        assert 'correct_token' in content

    def test_update_progress_marks_item_complete(self):
        """Test that update_progress marks the item as complete."""
        tasks_data = {
            "campaign1": {
                "info": {
                    "assignment": "task-based",
                    "template": "pointwise",
                }
            }
        }
        progress_data = {
            "campaign1": {
                "user1": {
                    "progress": [False, False, False],
                }
            }
        }
        update_progress("campaign1", "user1", tasks_data, progress_data, 1, {})
        assert progress_data["campaign1"]["user1"]["progress"] == [
            False, True, False]

    def test_reset_task_clears_progress(self):
        """Test that reset_task clears the progress."""
        tasks_data = {
            "campaign1": {
                "info": {
                    "assignment": "task-based",
                    "template": "pointwise",
                },
                "data": {
                    "user1": [
                        [{"src": "a", "tgt": "b"}],
                        [{"src": "c", "tgt": "d"}],
                    ]
                }
            }
        }
        progress_data = {
            "campaign1": {
                "user1": {
                    "progress": [True, True],
                    "time": 100.0,
                    "time_start": 1000,
                    "time_end": 2000,
                }
            }
        }
        reset_task("campaign1", "user1", tasks_data, progress_data)
        assert progress_data["campaign1"]["user1"]["progress"] == [
            False, False]
        assert progress_data["campaign1"]["user1"]["time"] == 0.0
        assert progress_data["campaign1"]["user1"]["time_start"] is None
        assert progress_data["campaign1"]["user1"]["time_end"] is None


class TestSingleStream:
    """Tests for single-stream assignment."""

    def test_get_next_item_returns_random_incomplete(self):
        """Test that single-stream returns a random incomplete item."""
        tasks_data = {
            "campaign1": {
                "info": {
                    "assignment": "single-stream",
                    "template": "pointwise",
                },
                "data": [
                    [{"src": "a", "tgt": "b"}],
                    [{"src": "c", "tgt": "d"}],
                    [{"src": "e", "tgt": "f"}],
                ]
            }
        }
        progress_data = {
            "campaign1": {
                "user1": {
                    "progress": [True, False, False],
                    "time": 0,
                    "token_correct": "abc",
                    "token_incorrect": "xyz",
                }
            }
        }
        response = get_next_item("campaign1", "user1",
                                 tasks_data, progress_data)
        assert response.status_code == 200
        content = response.body.decode()
        # Should return item 1 or 2 (incomplete items)
        assert '"item_i":1' in content or '"item_i":2' in content

    def test_singlestream_completed_returns_token(self):
        """Test that single-stream returns completion token when all items done."""
        tasks_data = {
            "campaign1": {
                "info": {
                    "assignment": "single-stream",
                    "template": "pointwise",
                },
                "data": [
                    [{"src": "a", "tgt": "b"}],
                ]
            }
        }
        progress_data = {
            "campaign1": {
                "user1": {
                    "progress": [True],
                    "time": 100,
                    "token_correct": "correct_token",
                    "token_incorrect": "wrong_token",
                }
            }
        }
        response = get_next_item("campaign1", "user1",
                                 tasks_data, progress_data)
        assert response.status_code == 200
        content = response.body.decode()
        assert '"status":"completed"' in content
        assert 'correct_token' in content

    def test_reset_task_resets_all_users(self):
        """Test that single-stream reset_task resets progress for all users."""
        tasks_data = {
            "campaign1": {
                "info": {
                    "assignment": "single-stream",
                    "template": "pointwise",
                },
                "data": [
                    [{"src": "a", "tgt": "b"}],
                    [{"src": "c", "tgt": "d"}],
                    [{"src": "e", "tgt": "f"}],
                ]
            }
        }
        progress_data = {
            "campaign1": {
                "user1": {
                    "progress": [True, True, False],
                    "time": 50.0,
                    "time_start": 1000,
                    "time_end": 2000,
                },
                "user2": {
                    "progress": [True, True, False],
                    "time": 75.0,
                    "time_start": 1100,
                    "time_end": 2100,
                }
            }
        }
        reset_task("campaign1", "user1", tasks_data, progress_data)
        # Both users' progress should be reset
        assert progress_data["campaign1"]["user1"]["progress"] == [
            False, False, False]
        assert progress_data["campaign1"]["user2"]["progress"] == [
            False, False, False]
        # Only user1's time should be reset
        assert progress_data["campaign1"]["user1"]["time"] == 0.0
        assert progress_data["campaign1"]["user1"]["time_start"] is None
        assert progress_data["campaign1"]["user2"]["time"] == 75.0

    def test_update_progress_updates_all_users(self):
        """Test that single-stream update_progress updates all users."""
        tasks_data = {
            "campaign1": {
                "info": {
                    "assignment": "single-stream",
                    "template": "pointwise",
                }
            }
        }
        progress_data = {
            "campaign1": {
                "user1": {
                    "progress": [False, False, False],
                },
                "user2": {
                    "progress": [False, False, False],
                }
            }
        }
        update_progress("campaign1", "user1", tasks_data, progress_data, 1, {})
        # Both users should have item 1 marked as complete
        assert progress_data["campaign1"]["user1"]["progress"] == [
            False, True, False]
        assert progress_data["campaign1"]["user2"]["progress"] == [
            False, True, False]