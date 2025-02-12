import tkinter as tk
import logging
from rich.logging import RichHandler
import customtkinter as ctk
import os

from settings_manager import SettingsManager
from ollama_service_manager import OllamaServiceManager, OllamaError
from processing_history import ProcessingHistory
from ui_components import create_model_indicators, create_scrolled_text, create_status_bar, create_toolbar, create_menu, update_output, handle_phase_error, reset_ui_state, clear_output, copy_to_clipboard, save_output, export_history, OutputHandler, sanitize_output
from processing_functions import analyze_prompt, generate_solutions, vet_and_refine, finalize_prompt, enhance_prompt, comprehensive_review, validate_models, verify_model_availability, retry_with_fallback

# Initialize logging first
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

# Make sure customtkinter's images are in the correct path
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)
os.environ["CUSTOMTKINTER_IMAGES_PATH"] = assets_dir

# Create global application state (only one instance)
app_state = ApplicationState()

OLLAMA_MODELS = {
    "analysis": "llama3.2:latest",      # Initial deep analysis
    "generation": "olmo2:13b",           # Creative solution generation
    "vetting": "deepseek-r1",            # Initial vetting
    "finalization": "deepseek-r1:14b",     # First round improvement
    "enhancement": "phi4:latest",         # Advanced enhancement
    "comprehensive": "phi4:latest",       # Initial comprehensive review
    "presenter": "deepseek-r1:14b",        # Final presentation cleanup
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
        self.processing_history = ProcessingHistory()
        self.settings_manager = SettingsManager()
        self.ollama_manager = OllamaServiceManager(self)

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
        # Update toolbar references if available
        if self.toolbar and ('input_text' in kwargs or 'output_text' in kwargs):
            self.toolbar.update_references(self.input_text, self.output_text)
        # Update menu references if available
        if self.menu_manager and ('input_text' in kwargs or 'output_text' in kwargs):
            self.menu_manager.update_references(self.input_text, self.output_text)

# Create global application state (only one instance)
app_state = ApplicationState()

def process_prompt():
    """Process the input prompt through the enhancement pipeline."""
    if app_state.is_processing:
        return
    app_state.is_processing = True
    def run_processing():
        try:
            # dummy processing steps:
            prompt = app_state.input_text.get("1.0", "end").strip() if app_state.input_text else ""
            update_output(PROGRESS_MESSAGES["start"])
            analysis = analyze_prompt(prompt, OLLAMA_MODELS["analysis"])
            update_output(PROGRESS_MESSAGES["analysis_done"])
            solutions = generate_solutions(analysis, OLLAMA_MODELS["generation"])
            update_output(PROGRESS_MESSAGES["generation_done"])
            vetted = vet_and_refine(solutions, OLLAMA_MODELS["vetting"])
            update_output(PROGRESS_MESSAGES["vetting_done"])
            final = finalize_prompt(vetted, prompt, OLLAMA_MODELS["finalization"])
            update_output(PROGRESS_MESSAGES["finalize_done"])
            enhanced = enhance_prompt(final, OLLAMA_MODELS["enhancement"])
            update_output(PROGRESS_MESSAGES["enhance_done"])
            comprehensive = comprehensive_review(prompt, analysis, solutions, vetted, final, enhanced, OLLAMA_MODELS["comprehensive"])
            update_output(comprehensive)
            update_output(PROGRESS_MESSAGES["complete"])
        except Exception as e:
            handle_phase_error("Processing", e, None, app_state.loading, "")
        finally:
            app_state.is_processing = False
    processing_thread = threading.Thread(target=run_processing)
    processing_thread.daemon = True
    processing_thread.start()

def main():
    """Main function."""
    root = tk.Tk()
    root.title("Prompt Enhancer")
    # Initialize global state UI elements
    app_state.initialize(root)
    app_state.status_bar = create_status_bar(root)
    input_text = create_scrolled_text(root, height=10, width=50)
    output_text = create_scrolled_text(root, height=10, width=50, readonly=True)
    app_state.input_text = input_text
    app_state.output_text = output_text
    toolbar = create_toolbar(root, input_text, output_text)
    toolbar.pack(pady=5)
    # Pack text widgets
    input_text.pack(pady=5, fill="both", expand=True)
    output_text.pack(pady=5, fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}")