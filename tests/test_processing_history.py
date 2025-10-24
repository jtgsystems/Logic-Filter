"""Tests for ProcessingHistory."""
from processing_history import ProcessingHistory


class TestProcessingHistory:
    """Test ProcessingHistory functionality."""

    def test_init(self):
        """Test initialization."""
        history = ProcessingHistory()
        assert history.history == []
        assert history.current_index == -1
        assert history.max_history == 50

    def test_add_entry(self):
        """Test adding entries to history."""
        history = ProcessingHistory()
        history.add("input1", "output1")

        assert len(history.history) == 1
        assert history.current_index == 0
        assert history.history[0]["input"] == "input1"
        assert history.history[0]["output"] == "output1"

    def test_max_history_limit(self):
        """Test that history respects max limit."""
        history = ProcessingHistory()
        history.max_history = 3

        for i in range(5):
            history.add(f"input{i}", f"output{i}")

        assert len(history.history) == 3
        assert history.history[0]["input"] == "input2"
        assert history.history[-1]["input"] == "input4"

    def test_undo_redo(self):
        """Test undo and redo functionality."""
        history = ProcessingHistory()
        history.add("input1", "output1")
        history.add("input2", "output2")
        history.add("input3", "output3")

        # Test undo
        assert history.can_undo()
        entry = history.undo()
        assert entry["input"] == "input2"

        # Test redo
        assert history.can_redo()
        entry = history.redo()
        assert entry["input"] == "input3"

    def test_clear(self):
        """Test clearing history."""
        history = ProcessingHistory()
        history.add("input1", "output1")
        history.add("input2", "output2")

        history.clear()

        assert len(history.history) == 0
        assert history.current_index == -1
        assert not history.can_undo()
        assert not history.can_redo()

    def test_get_current(self):
        """Test getting current entry."""
        history = ProcessingHistory()
        assert history.get_current() is None

        history.add("input1", "output1")
        current = history.get_current()

        assert current is not None
        assert current["input"] == "input1"
        assert current["output"] == "output1"
