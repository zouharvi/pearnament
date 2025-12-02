"""Tests for utility functions."""

from pearmut.utils import highlight_differences


class TestHighlightDifferences:
    """Tests for highlight_differences function."""

    def test_identical_strings(self):
        """Test that identical strings have no highlighting."""
        a, b = highlight_differences("hello", "hello")
        assert a == "hello"
        assert b == "hello"

    def test_completely_different_strings(self):
        """Test that completely different strings are highlighted."""
        a, b = highlight_differences("hello", "world")
        assert '<span class="difference">' in a
        assert '<span class="difference">' in b

    def test_partial_difference(self):
        """Test strings with partial differences."""
        a, b = highlight_differences("hello world", "hello there")
        assert "hello " in a
        assert "hello " in b
        assert '<span class="difference">' in a
        assert '<span class="difference">' in b

    def test_empty_strings(self):
        """Test empty strings."""
        a, b = highlight_differences("", "")
        assert a == ""
        assert b == ""

    def test_one_empty_string(self):
        """Test with one empty string."""
        a, b = highlight_differences("hello", "")
        assert '<span class="difference">hello</span>' in a
        assert b == ""

    def test_insertion(self):
        """Test string with insertion - small insertions are ignored."""
        a, b = highlight_differences("abc", "abxc")
        # Small differences (<=2 chars) are not highlighted
        assert a == "abc"
        assert b == "abxc"

    def test_large_insertion(self):
        """Test string with larger insertion that gets highlighted."""
        a, b = highlight_differences("abc", "ab12345c")
        # Larger differences (>2 chars) are highlighted
        assert '<span class="difference">' in b
