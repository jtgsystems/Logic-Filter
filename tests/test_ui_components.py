"""Tests for UI components."""
from ui_components import sanitize_output


class TestUIComponents:
    """Test UI component functions."""

    def test_sanitize_output_removes_markdown(self):
        """Test that sanitize_output removes markdown."""
        text = "```python\nprint('hello')\n```"
        result = sanitize_output(text)
        assert "```" not in result
        assert "python" in result
        assert "print('hello')" in result

    def test_sanitize_output_removes_formatting(self):
        """Test that sanitize_output removes formatting."""
        text = "**bold** and `code` and #heading"
        result = sanitize_output(text)
        assert "**" not in result
        assert "`" not in result
        assert "#" not in result
        assert "bold" in result
        assert "code" in result
        assert "heading" in result

    def test_sanitize_output_handles_present_to_user(self):
        """Test that sanitize_output handles PRESENT TO USER marker."""
        text = "Some preamble\nPRESENT TO USER: Final output"
        result = sanitize_output(text)
        assert "Some preamble" not in result
        assert "Final output" in result

    def test_sanitize_output_empty_string(self):
        """Test that sanitize_output handles empty strings."""
        assert sanitize_output("") == ""
        assert sanitize_output(None) == ""

    def test_sanitize_output_whitespace_cleanup(self):
        """Test that sanitize_output cleans up whitespace."""
        text = "  line1  \n\n  line2  \n\n\n"
        result = sanitize_output(text)
        lines = result.split("\n")
        assert len([line for line in lines if line]) == 2
        assert "line1" in result
        assert "line2" in result
