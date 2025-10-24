"""Tests for SettingsManager."""
import os
import tempfile

from settings_manager import SettingsManager


class TestSettingsManager:
    """Test SettingsManager functionality."""

    def test_init_creates_default_settings(self):
        """Test that initialization creates default settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = os.path.join(tmpdir, "test_settings.json")
            manager = SettingsManager()
            manager.settings_file = settings_file
            assert manager.settings is not None
            assert "theme" in manager.settings
            assert "font_size" in manager.settings

    def test_save_and_load_settings(self):
        """Test saving and loading settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = os.path.join(tmpdir, "test_settings.json")
            manager = SettingsManager()
            manager.settings_file = settings_file

            # Set some values
            manager.set("theme", "light")
            manager.set("font_size", 16)
            manager.save_settings()

            # Create new manager and load
            new_manager = SettingsManager()
            new_manager.settings_file = settings_file
            new_manager.settings = new_manager.load_settings()

            assert new_manager.get("theme") == "light"
            assert new_manager.get("font_size") == 16

    def test_get_with_default(self):
        """Test getting settings with default values."""
        manager = SettingsManager()
        assert manager.get("nonexistent_key", "default_value") == "default_value"

    def test_update_window_state(self):
        """Test updating window state."""
        manager = SettingsManager()
        manager.update_window_state("800x600+100+100", True)

        assert manager.settings["window"]["geometry"] == "800x600+100+100"
        assert manager.settings["window"]["zoomed"] is True
