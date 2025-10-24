import logging
import os
import threading
import tkinter as tk

import customtkinter as ctk
from rich.logging import RichHandler

from api import app as flask_app  # Import the Flask app instance
from ollama_service_manager import OllamaServiceManager
from processing_functions import (
    analyze_prompt,
    comprehensive_review,
    enhance_prompt,
    finalize_prompt,
    generate_solutions,
    vet_and_refine,
)
from processing_history import ProcessingHistory
from settings_manager import SettingsManager
from ui_components import (
    LoadingIndicator,
    create_menu,
    create_model_indicators,
    create_scrolled_text,
    create_status_bar,
    create_toolbar,
    handle_phase_error,
    update_output,
)

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

# Constants
OLLAMA_MODELS = {
    "analysis": "llama3.2:latest",      # Initial deep analysis
    "generation": "olmo2:13b",           # Creative solution generation
    "vetting": "deepseek-r1",            # Initial vetting
    "finalization": "deepseek-r1:14b",   # First round improvement
    "enhancement": "phi4:latest",        # Advanced enhancement
    "comprehensive": "phi4:latest",      # Initial comprehensive review
    "presenter": "deepseek-r1:14b",      # Final presentation cleanup
}

FALLBACK_ORDER = {
    "llama3.2:latest": ["deepseek-r1", "phi4:latest"],
    "olmo2:13b": ["deepseek-r1:14b", "phi4:latest"],
    "deepseek-r1": ["phi4:latest", "llama3.2:latest"],
    "deepseek-r1:14b": ["phi4:latest", "deepseek-r1"],
    "phi4:latest": ["deepseek-r1:14b", "llama3.2:latest"],
}

PROGRESS_MESSAGES = {
    "start": "Processing prompt...\n",
    "analyzing": "Phase 1/6: Analysis\n",
    "analysis_done": "Analysis complete.\n\n",
    "generating": "Phase 2/6: Generation\n",
    "generation_done": "Generation complete.\n\n",
    "vetting": "Phase 3/6: Vetting\n",
    "vetting_done": "Vetting complete.\n\n",
    "finalizing": "Phase 4/6: Finalization\n",
    "finalize_done": "Finalization complete.\n\n",
    "enhancing": "Phase 5/6: Enhancement\n",
    "enhance_done": "Enhancement complete.\n\n",
    "comprehensive": "Phase 6/6: Review\n",
    "complete": "Process complete.\n\n",
}

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
            prompt = app_state.input_text.get("1.0", "end").strip()
            if not prompt:
                update_output("Error: No prompt entered.", is_error=True)
                return

            # Run the enhancement pipeline
            app_state.loading.start(0)
            update_output(PROGRESS_MESSAGES["start"])

            analysis = analyze_prompt(prompt, OLLAMA_MODELS["analysis"])
            app_state.loading.start(20)
            update_output(PROGRESS_MESSAGES["analysis_done"] + analysis)

            solutions = generate_solutions(analysis, OLLAMA_MODELS["generation"])
            app_state.loading.start(40)
            update_output(PROGRESS_MESSAGES["generation_done"] + solutions)

            vetted = vet_and_refine(solutions, OLLAMA_MODELS["vetting"])
            app_state.loading.start(60)
            update_output(PROGRESS_MESSAGES["vetting_done"] + vetted)

            final = finalize_prompt(vetted, prompt, OLLAMA_MODELS["finalization"])
            app_state.loading.start(80)
            update_output(PROGRESS_MESSAGES["finalize_done"] + final)

            enhanced = enhance_prompt(final, OLLAMA_MODELS["enhancement"])
            app_state.loading.start(90)
            update_output(PROGRESS_MESSAGES["enhance_done"] + enhanced)

            comprehensive = comprehensive_review(
                prompt, analysis, solutions, vetted,
                final, enhanced, OLLAMA_MODELS["comprehensive"]
            )
            app_state.loading.start(100)
            update_output(comprehensive)
            update_output(PROGRESS_MESSAGES["complete"])

            # Store in history
            app_state.processing_history.add(prompt, comprehensive)

        except Exception as e:
            error_msg = handle_phase_error("Processing", e, None, app_state.loading, "")
            update_output(error_msg, is_error=True)
        finally:
            app_state.is_processing = False
            app_state.loading.stop()
            app_state.status_bar.set_status("Ready")

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
    toolbar = create_toolbar(main_container)
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
    app_state.menu_manager = create_menu(root)

# Create global application state
app_state = ApplicationState()

def start_flask_app():
    """Start the Flask app in a separate thread."""
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    flask_app.run(debug=debug_mode, use_reloader=False, host='127.0.0.1', port=5000)

def main():
    """Main entry point of the application."""
    root = tk.Tk()
    app_state.initialize(root)

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
