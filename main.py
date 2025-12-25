import tkinter as tk
import logging
import os
import threading
from rich.logging import RichHandler
import customtkinter as ctk
from settings_manager import SettingsManager
from ollama_service_manager import OllamaServiceManager, OllamaError
from processing_history import ProcessingHistory
from ui_components import (
    create_model_indicators,
    create_scrolled_text,
    create_status_bar,
    create_toolbar,
    create_menu,
    LoadingIndicator,
    update_output,
    handle_phase_error
)
from processing_functions import (
    run_full_pipeline,
    validate_models
)
from config import OLLAMA_MODELS
from ui_components import set_output_widget

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("prompt_enhancer")

# Initialize customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ApplicationState:
    """Global application state manager"""
    def __init__(self):
        self.root = None
        self.input_text = None
        self.output_text = None
        self.status_bar = None
        self.loading = None
        self.processing_history = None
        self.settings_manager = None
        self.toolbar = None
        self.menu_manager = None
        self.model_indicators = None
        self.ollama_manager = None
        self.is_processing = False

    def initialize(self, root):
        """Initialize application state with root window"""
        self.root = root
        self.settings_manager = SettingsManager()
        self.processing_history = ProcessingHistory()
        self.processing_history.max_history = self.settings_manager.get("max_history", 50)
        self.ollama_manager = OllamaServiceManager(self)
        self.loading = LoadingIndicator(root)

    def reset_indicators(self):
        """Reset all model indicators to inactive state"""
        if self.model_indicators:
            for label in self.model_indicators.values():
                label.configure(text_color="gray")

    def set_active_model(self, model_type):
        """Set a model indicator as active"""
        if self.model_indicators and model_type in self.model_indicators:
            self.reset_indicators()
            self.model_indicators[model_type].configure(text_color="#4a90e2")

    def update_references(self, **kwargs):
        """Update component references"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

def process_prompt():
    """Process the input prompt through the enhancement pipeline."""
    if app_state.is_processing:
        return

    app_state.is_processing = True
    def run_processing():
        try:
            def ui_update(text, is_error=False):
                if app_state.root:
                    app_state.root.after(0, lambda: update_output(text, is_error))

            prompt = app_state.input_text.get("1.0", "end").strip()
            if not prompt:
                ui_update("Error: No prompt entered.", is_error=True)
                return

            if not app_state.ollama_manager.initialize_ollama():
                ui_update("Error: Ollama is not ready.", is_error=True)
                return

            unavailable = validate_models()
            if unavailable:
                missing = ", ".join([m for _, m in unavailable])
                ui_update(f"Error: Missing models: {missing}", is_error=True)
                return

            if app_state.root:
                app_state.root.after(0, lambda: app_state.status_bar.set_status("Processing"))
                app_state.root.after(0, lambda: app_state.loading.start(0))

            output_chunks = []
            phase_to_progress = {
                "analysis_done": 20,
                "generation_done": 40,
                "vetting_done": 60,
                "finalize_done": 80,
                "enhance_done": 90,
                "complete": 100,
            }
            phase_to_model = {
                "analysis_done": "analysis",
                "generation_done": "generation",
                "vetting_done": "vetting",
                "finalize_done": "finalization",
                "enhance_done": "enhancement",
                "complete": "comprehensive",
            }

            def progress_cb(phase, message, content):
                if message:
                    output_chunks.append(message.strip())
                if content:
                    output_chunks.append(content)

                def _ui_update():
                    if phase in phase_to_model:
                        app_state.set_active_model(phase_to_model[phase])
                    if phase in phase_to_progress:
                        app_state.loading.start(phase_to_progress[phase])
                    update_output("\n\n".join([c for c in output_chunks if c]))

                if app_state.root:
                    app_state.root.after(0, _ui_update)

            mode = app_state.settings_manager.get("mode", None) if app_state.settings_manager else None
            results = run_full_pipeline(prompt, progress_cb=progress_cb, mode=mode)

            # Store in history
            app_state.processing_history.add(prompt, results.get("comprehensive", ""))

        except Exception as e:
            error_msg = handle_phase_error("Processing", e, None, None, "")
            if app_state.root:
                app_state.root.after(0, lambda: update_output(error_msg, is_error=True))
        finally:
            app_state.is_processing = False
            if app_state.root:
                app_state.root.after(0, app_state.loading.stop)
                app_state.root.after(0, lambda: app_state.status_bar.set_status("Ready"))

    processing_thread = threading.Thread(target=run_processing)
    processing_thread.daemon = True
    processing_thread.start()

def setup_main_window(root):
    """Set up the main application window"""
    root.title("Prompt Enhancer")

    # Create and configure the main container
    main_container = ctk.CTkFrame(root)
    main_container.pack(fill="both", expand=True, padx=10, pady=10)

    # Create model indicators
    indicators_frame, indicators = create_model_indicators(main_container, OLLAMA_MODELS.keys())
    indicators_frame.pack(fill="x", pady=(0, 10))
    app_state.model_indicators = indicators

    # Create toolbar
    toolbar = create_toolbar(main_container, input_text, output_text)
    toolbar.pack(fill="x", pady=(0, 10))
    app_state.toolbar = toolbar

    # Create text areas
    input_frame = ctk.CTkFrame(main_container)
    input_frame.pack(fill="both", expand=True)

    input_label = ctk.CTkLabel(input_frame, text="Input Prompt:")
    input_label.pack(anchor="w")

    input_text = create_scrolled_text(input_frame, height=200)
    input_text.pack(fill="both", expand=True, pady=(5, 10))

    output_frame = ctk.CTkFrame(main_container)
    output_frame.pack(fill="both", expand=True)

    output_label = ctk.CTkLabel(output_frame, text="Enhanced Output:")
    output_label.pack(anchor="w")

    output_text = create_scrolled_text(output_frame, height=200, readonly=True)
    output_text.pack(fill="both", expand=True, pady=(5, 10))
    set_output_widget(output_text)

    # Create process button
    process_btn = ctk.CTkButton(
        main_container,
        text="Process Prompt",
        command=process_prompt,
        height=40
    )
    process_btn.pack(pady=10)

    # Create status bar
    status_bar = create_status_bar(main_container)
    status_bar.pack(fill="x", pady=(10, 0))

    # Update application state
    app_state.input_text = input_text
    app_state.output_text = output_text
    app_state.status_bar = status_bar

    # Set up window state
    root.update_idletasks()
    width = 800
    height = 900
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Create menu
    app_state.menu_manager = create_menu(root, input_text, output_text)

# Create global application state
app_state = ApplicationState()

def start_flask_app():
    """Start the Flask app in a separate thread."""
    from api import app as flask_app
    flask_app.run(debug=True, use_reloader=False)

def main():
    """Main entry point of the application."""
    root = tk.Tk()
    app_state.initialize(root)
    ctk.set_appearance_mode(app_state.settings_manager.get("theme", "dark"))

    # Make sure customtkinter's images are in the correct path
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    os.environ["CUSTOMTKINTER_IMAGES_PATH"] = assets_dir

    # Set up the main window
    setup_main_window(root)

    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}")
