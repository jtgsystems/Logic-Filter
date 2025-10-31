import requests
import time
import logging
from settings_manager import SettingsManager

logger = logging.getLogger("prompt_enhancer")

_manager = None

def get_ollama_manager(app_state=None):
    """Get the singleton instance of the OllamaServiceManager."""
    global _manager
    if _manager is None:
        _manager = OllamaServiceManager(app_state)
    return _manager

class OllamaError(Exception):
    """Custom exception for Ollama-related errors."""
    pass

class OllamaServiceManager:
    """Manages Ollama service and model availability"""
    def __init__(self, app_state=None):
        self.app_state = app_state
        self.ollama_ready = False
        self.models_loaded = False
        self.ollama_module = None
        self.check_interval = 30000  # 30 seconds between checks
        self._last_check = 0
        self._start_service_check()
        
    def _start_service_check(self):
        """Start periodic service checking"""
        if self.app_state and self.app_state.root:
            self.check_service_status()
        
    def check_ollama_service(self):
        """Check if Ollama service is running and accessible."""
        timeout = 2
        if self.app_state and hasattr(self.app_state, 'settings_manager') and self.app_state.settings_manager:
            timeout = self.app_state.settings_manager.get('request_timeout', 2)
        try:
            response = requests.get(
                "http://localhost:11434/api/health",
                timeout=timeout
            )
            if response.status_code == 200:
                return True
            logger.warning(f"Ollama health check failed with status {response.status_code}")
            return False
        except requests.exceptions.Timeout:
            logger.warning("Ollama health check timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("Failed to connect to Ollama service")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking Ollama service: {e}")
            return False

    def initialize_ollama(self):
        """Initialize Ollama service and models"""
        if self.check_ollama_service():
            try:
                if self.ollama_module is None:
                    import ollama
                    self.ollama_module = ollama
                self.ollama_ready = True
                if self.app_state and hasattr(self.app_state, 'status_bar') and self.app_state.status_bar:
                    self.app_state.status_bar.set_model_status("Connected")
                    self.app_state.status_bar.set_status("Ollama service ready")
                return True
            except ImportError:
                if self.app_state and hasattr(self.app_state, 'status_bar') and self.app_state.status_bar:
                    self.app_state.status_bar.set_model_status("Not installed", is_error=True)
                    self.app_state.status_bar.set_status("Please install Ollama", is_error=True)
                return False
        else:
            if self.app_state and hasattr(self.app_state, 'status_bar') and self.app_state.status_bar:
                self.app_state.status_bar.set_model_status("Not running", is_error=True)
                self.app_state.status_bar.set_status("Start Ollama service", is_error=True)
            return False

    def check_service_status(self):
        """Check Ollama service status periodically"""
        current_time = time.time() * 1000
        
        if current_time - self._last_check >= self.check_interval:
            self._last_check = current_time
            if not self.ollama_ready:
                if self.initialize_ollama():
                    if self.app_state and hasattr(self.app_state, 'status_bar') and self.app_state.status_bar:
                        self.app_state.status_bar.set_status("Ollama connected")
            
        if not self.ollama_ready and self.app_state and self.app_state.root:
            self.app_state.root.after(self.check_interval, self.check_service_status)

    def chat(self, *args, **kwargs):
        """Wrapper for ollama.chat that ensures service is initialized"""
        if not self.ollama_ready:
            if not self.initialize_ollama():
                raise OllamaError("Ollama service not ready")
        return self.ollama_module.chat(*args, **kwargs)
        
    def verify_model(self, model_name):
        """Verify if a specific model is available"""
        try:
            if not self.ollama_ready:
                return False
                
            self.chat(
                model=model_name, 
                messages=[{"role": "user", "content": "test"}],
                options={"timeout": 5000}
            )
            return True
        except Exception as e:
            return False
