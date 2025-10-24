import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger("prompt_enhancer")

class SettingsManager:
    """Manages application settings."""
    def __init__(self):
        self.settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
        self.default_settings = {
            'theme': 'dark',
            'font_size': 12,
            'max_history': 50,
            'autosave': True,
            'show_model_indicators': True,
            'save_window_state': True,
            'window': {
                'geometry': '1024x768',
                'zoomed': False
            }
        }
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file) as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all settings exist
                    return {**self.default_settings, **loaded}
            return self.default_settings.copy()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return self.default_settings.copy()

    def save_settings(self) -> None:
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        try:
            self.settings[key] = value
            if self.get('autosave', True):
                self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set setting {key}: {e}")

    def update_window_state(self, geometry: str, zoomed: bool) -> None:
        """Update window state settings."""
        self.settings['window'] = {
            'geometry': geometry,
            'zoomed': zoomed
        }
        if self.get('autosave', True):
            self.save_settings()
