import threading
from datetime import datetime


class ProcessingHistory:
    """Manages processing history and undo/redo functionality"""
    def __init__(self):
        self.history = []
        self.current_index = -1
        self.max_history = 50
        self._lock = threading.Lock()

    def add(self, input_text, output_text):
        """Add a new processing result to history thread-safely"""
        with self._lock:
            # Remove any redo entries
            self.history = self.history[:self.current_index + 1]

            entry = {
                'input': input_text,
                'output': output_text,
                'timestamp': datetime.now().isoformat()
            }

            self.history.append(entry)
            self.current_index += 1

            # Trim history if too long
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
                self.current_index = len(self.history) - 1

    def can_undo(self):
        """Check if undo is available"""
        return self.current_index > 0

    def can_redo(self):
        """Check if redo is available"""
        return self.current_index < len(self.history) - 1

    def undo(self):
        """Get previous processing result"""
        with self._lock:
            if self.can_undo():
                self.current_index -= 1
                return self.history[self.current_index]
            return None

    def redo(self):
        """Get next processing result"""
        with self._lock:
            if self.can_redo():
                self.current_index += 1
                return self.history[self.current_index]
            return None

    def get_current(self):
        """Get current history entry"""
        with self._lock:
            if 0 <= self.current_index < len(self.history):
                return self.history[self.current_index]
            return None

    def clear(self):
        """Clear history"""
        with self._lock:
            self.history = []
            self.current_index = -1
