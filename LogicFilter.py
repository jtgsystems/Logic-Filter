import time
import os
import sys
import json
import logging
import threading
import asyncio
import requests
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox

import customtkinter as ctk
from rich.logging import RichHandler
from ttkthemes import ThemedStyle

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

# Dummy import for ollama module
try:
    import ollama
except ImportError:
    ollama = None  # In case ollama is not installed, handle accordingly

class OllamaError(Exception):
    """Custom exception for Ollama-related errors."""
    pass

class ProcessingHistory:
    """Manages processing history and undo/redo functionality"""
    def __init__(self):
        pass
    def add(self, input_text, output_text):
        pass
    def can_undo(self):
        return False
    def can_redo(self):
        return False
    def undo(self):
        pass
    def redo(self):
        pass
    def get_current(self):
        return None
    def clear(self):
        pass

class SettingsManager:
    """Manages application settings."""
    def __init__(self):
        self.settings = {}
    def load_settings(self):
        pass
    def save_settings(self):
        pass
    def get(self, key, default=None):
        return self.settings.get(key, default)
    def set(self, key, value):
        self.settings[key] = value
    def update_window_state(self, geometry, zoomed):
        pass

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

class OllamaServiceManager:
    """Manages Ollama service and model availability"""
    def __init__(self, app_state):
        self.app_state = app_state
        self.ollama_ready = False
        self.models_loaded = False
        self.ollama_module = None
        self.check_interval = 30000  # 30 seconds between checks
        self._last_check = 0
        self._start_service_check()

    def _start_service_check(self):
        """Start periodic service checking"""
        if self.app_state.root:
            self.check_service_status()

    def check_ollama_service(self):
        """Check if Ollama service is running and accessible."""
        try:
            response = requests.get("http://localhost:11434/api/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def initialize_ollama(self):
        """Initialize Ollama service and models"""
        if self.check_ollama_service():
            try:
                if self.ollama_module is None:
                    if ollama is not None:
                        self.ollama_module = ollama
                    else:
                        raise ImportError("ollama module not available")
                self.ollama_ready = True
                if self.app_state.status_bar:
                    self.app_state.status_bar.set_model_status("Connected")
                    self.app_state.status_bar.set_status("Ollama service ready")
                return True
            except ImportError:
                if self.app_state.status_bar:
                    self.app_state.status_bar.set_model_status("Not installed", is_error=True)
                    self.app_state.status_bar.set_status("Please install Ollama", is_error=True)
                return False
        else:
            if self.app_state.status_bar:
                self.app_state.status_bar.set_model_status("Not running", is_error=True)
                self.app_state.status_bar.set_status("Start Ollama service", is_error=True)
            return False

    def check_service_status(self):
        """Check Ollama service status periodically"""
        current_time = time.time() * 1000  # Convert to milliseconds
        if current_time - self._last_check >= self.check_interval:
            self._last_check = current_time
            if not self.ollama_ready:
                if self.initialize_ollama():
                    if self.app_state.status_bar:
                        self.app_state.status_bar.set_status("Ollama connected")
        if not self.ollama_ready and self.app_state.root:
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
            response = self.chat(
                model=model_name, 
                messages=[{"role": "user", "content": "test"}],
                options={"timeout": 5000}
            )
            return True
        except Exception as e:
            return False

def configure_ttk_style():
    style = ThemedStyle()
    style.set_theme("equilux")  # Dark theme that matches customtkinter
    return style

def verify_model_availability(model_name):
    """Verify if an Ollama model is available."""
    try:
        if not app_state.ollama_manager.ollama_ready:
            return False
        app_state.ollama_manager.chat(
            model=model_name, 
            messages=[{"role": "user", "content": "test"}],
            options={"timeout": 5000}
        )
        return True
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str:
            raise OllamaError("Cannot connect to Ollama service. Is it running?")
        elif "timeout" in error_str:
            raise OllamaError(f"Model {model_name} timed out")
        else:
            logger.error(f"Model {model_name} is not available: {str(e)}")
            return False

def validate_models():
    """Validate all required models are available."""
    if not app_state.ollama_manager.ollama_ready:
        return []  # don't validate if service isn't ready
    unavailable_models = []
    connection_error = None
    for purpose, model in OLLAMA_MODELS.items():
        try:
            if not verify_model_availability(model):
                unavailable_models.append((purpose, model))
        except OllamaError as e:
            if "cannot connect" in str(e).lower():
                connection_error = str(e)
                break
            unavailable_models.append((purpose, model))
    if connection_error:
        raise OllamaError(connection_error)
    return unavailable_models

def analyze_prompt(prompt, model_name):
    """Analyzes the initial prompt."""
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Analyze this prompt: '{prompt}'\n\n"
                    "Focus on:\n"
                    "1. Core requirements and goals\n"
                    "2. Key components needed\n"
                    "3. Specific constraints or parameters\n"
                    "4. Expected output format\n"
                    "5. Quality criteria\n\n"
                    "Provide a clear, focused analysis that will help in "
                    "improving this exact prompt. Stay focused on the task "
                    "and avoid going off on tangents."
                )
            }
        ]
        response = app_state.ollama_manager.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise OllamaError(f"Analysis failed: {str(e)}")

def generate_solutions(analysis, model_name):
    """Generates potential improvements based on analysis."""
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Based on this analysis: '{analysis}'\n\n"
                    "Generate specific improvements that:\n"
                    "1. Address identified issues\n"
                    "2. Enhance clarity and specificity\n"
                    "3. Add necessary structure\n"
                    "4. Maintain focus on core goals\n"
                    "5. Consider all quality criteria\n\n"
                    "Important: Generate practical, focused improvements "
                    "that directly enhance the prompt. Avoid theoretical "
                    "discussions or tangents."
                )
            }
        ]
        response = app_state.ollama_manager.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during solution generation: {e}")
        raise OllamaError(f"Solution generation failed: {str(e)}")

def vet_and_refine(improvements, model_name):
    """Reviews and validates the suggested improvements."""
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    "Review these suggested improvements: "
                    f"'{improvements}'\n\n"
                    "Evaluate how well they enhance the original prompt:\n"
                    "1. Do they address core requirements?\n"
                    "2. Are they clear and specific?\n"
                    "3. Do they maintain focus on the task?\n"
                    "4. Are they practical and implementable?\n\n"
                    "Important: Focus on validating improvements that "
                    "directly enhance the original prompt. Flag any "
                    "suggestions that go off-topic or deviate from the "
                    "main goal."
                )
            }
        ]
        response = app_state.ollama_manager.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during vetting: {e}")
        raise OllamaError(f"Vetting failed: {str(e)}")

def finalize_prompt(vetting_report, original_prompt, model_name):
    """Creates improved version incorporating validated enhancements."""
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Original Prompt: {original_prompt}\n"
                    f"Validated Improvements: {vetting_report}\n\n"
                    "Create an improved version that:\n"
                    "1. Maintains the original goal\n"
                    "2. Incorporates validated improvements\n"
                    "3. Uses clear, specific language\n"
                    "4. Adds necessary structure\n"
                    "5. Includes any required constraints\n\n"
                    "Important: Stay focused on the original task. Return only "
                    "the improved version of the input prompt."
                )
            }
        ]
        response = app_state.ollama_manager.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during finalization: {e}")
        raise OllamaError(f"Finalization failed: {str(e)}")

def enhance_prompt(final_prompt, model_name):
    """Refines and polishes the improved prompt."""
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    "Polish and refine this prompt:\n\n"
                    f"{final_prompt}\n\n"
                    "Focus on:\n"
                    "1. Making instructions crystal clear\n"
                    "2. Adding any missing details, try to find at least 10\n"
                    "3. Improving structure\n"
                    "4. Ensuring completeness\n"
                    "5. Maintaining focus\n\n"
                    "Important: Stay focused on improving THIS prompt. "
                    "Do NOT create examples or add unrelated content. "
                    "Return ONLY the polished version."
                )
            }
        ]
        response = app_state.ollama_manager.chat(model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during enhancement: {e}")
        raise OllamaError(f"Enhancement failed: {str(e)}")

def comprehensive_review(
    original_prompt,
    analysis_report,
    solutions,
    vetting_report,
    final_prompt,
    enhanced_prompt,
    model_name
):
    """Creates final version and ensures clean presentation."""
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    "Review all versions of this prompt and create an improved version that combines the best elements:\n\n"
                    f"Original: {original_prompt}\n"
                    f"Analysis: {analysis_report}\n"
                    f"Solutions: {solutions}\n"
                    f"Vetting: {vetting_report}\n"
                    f"Final: {final_prompt}\n"
                    f"Enhanced: {enhanced_prompt}\n\n"
                    "Create a refined version that maintains the core intent while maximizing clarity and effectiveness."
                )
            }
        ]
        response = app_state.ollama_manager.chat(model_name, messages=messages)
        improved = response["message"]["content"]
        # Optionally, you can add a second stage using a different model here.
        return improved
    except Exception as e:
        logger.error(f"Error during comprehensive review: {e}")
        raise OllamaError(f"Comprehensive review failed: {str(e)}")

def create_model_indicators(parent):
    """Creates a frame with model status indicators."""
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="x", pady=(0, 10))
    indicators = {}
    for model_type in OLLAMA_MODELS:
        label = ctk.CTkLabel(frame, text=model_type, text_color="gray")
        label.pack(side="left", padx=5)
        indicators[model_type] = label
    app_state.model_indicators = indicators
    return frame

def create_scrolled_text(parent, height=10, width=50, readonly=False):
    """Helper function to create a Text widget with a scrollbar."""
    frame = ctk.CTkFrame(parent)
    text_widget = ctk.CTkTextbox(
        frame,
        height=height,
        width=width,
        wrap="word",
        font=("Arial", 12)
    )
    if readonly:
        text_widget.configure(state="disabled")
    text_widget.pack(fill="both", expand=True)
    return text_widget

def retry_with_fallback(func, *args, max_retries=3, fallback_model=None):
    """Retry a function with fallback model if available."""
    last_error = None
    current_model = args[-1]  # assume last arg is model name
    for attempt in range(max_retries):
        try:
            return func(*args)
        except Exception as e:
            last_error = e
    if current_model in FALLBACK_ORDER and fallback_model:
        for model in FALLBACK_ORDER[current_model]:
            try:
                new_args = list(args)
                new_args[-1] = model
                return func(*new_args)
            except Exception as e:
                last_error = e
    raise OllamaError(f"Operation failed after all attempts: {str(last_error)}")

class ProgressTracker:
    """Tracks progress through processing phases"""
    def __init__(self):
        self.phase = None
    def update(self, phase):
        self.phase = phase
    def get_progress(self):
        return self.phase

class LoadingIndicator:
    """Animated loading indicator with improved performance"""
    def __init__(self, parent):
        self.parent = parent
        self.label = ctk.CTkLabel(parent, text="Loading...")
        self.label.pack()
    def start(self, progress=0):
        self.label.configure(text=f"Loading... {progress}%")
    def _start_animation(self):
        pass
    def stop(self):
        self.label.configure(text="Stopped")
    def update_label(self, text):
        self.label.configure(text=text)
    def destroy(self):
        self.label.destroy()

class ThemeManager:
    """Manages application theming"""
    @staticmethod
    def apply_theme(theme):
        pass

    @staticmethod
    def get_current_theme():
        return "dark"

class StatusBar(ctk.CTkFrame):
    """Enhanced status bar with multiple indicators and throttled updates"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.status_label = ctk.CTkLabel(self, text="Ready")
        self.status_label.pack(side="left")
    def setup_indicators(self):
        pass
    def toggle_theme(self):
        pass
    def _schedule_memory_update(self):
        pass
    def _update_memory(self):
        pass
    def set_model_status(self, status, is_error=False):
        self.status_label.configure(text=f"Model: {status}", text_color=("red" if is_error else "green"))
    def set_status(self, text, is_error=False):
        self.status_label.configure(text=text, text_color=("red" if is_error else "green"))
    def destroy(self):
        self.destroy()

def create_status_bar(parent):
    """Create status bar with theme toggle and connection status."""
    status_bar = StatusBar(parent)
    status_bar.pack(fill="x", side="bottom", pady=(5, 0))
    return status_bar

class Toolbar(ctk.CTkFrame):
    """Enhanced toolbar with updatable references"""
    def __init__(self, parent, input_text=None, output_text=None):
        super().__init__(parent)
        self.input_text = input_text
        self.output_text = output_text
        self.setup_ui()
    def setup_ui(self):
        # Create dummy buttons
        btn_new = ctk.CTkButton(self, text="New", command=self.new_document)
        btn_new.pack(side="left", padx=2)
    def update_references(self, input_text, output_text):
        self.input_text = input_text
        self.output_text = output_text
    def new_document(self):
        if self.input_text:
            self.input_text.delete("1.0", "end")
    def clear_output(self):
        if self.output_text:
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.configure(state="disabled")
    def copy_output(self):
        if self.output_text and app_state.root:
            app_state.root.clipboard_clear()
            app_state.root.clipboard_append(self.output_text.get("1.0", "end").strip())
    def save_output(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.output_text.get("1.0", "end"))
    def export_history(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"history": []}))

def create_toolbar(parent, input_text, output_text):
    """Create toolbar with common actions."""
    return Toolbar(parent, input_text, output_text)

class MenuManager:
    """Manages application menus and keyboard shortcuts"""
    def __init__(self, root, input_text=None, output_text=None):
        self.root = root
        self.input_text = input_text
        self.output_text = output_text
        self.create_menu()
        self.bind_shortcuts()
    def update_references(self, input_text, output_text):
        self.input_text = input_text
        self.output_text = output_text
    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_document)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)
    def bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_document())
    def new_document(self):
        if self.input_text:
            self.input_text.delete("1.0", "end")
    def clear_output(self):
        if self.output_text:
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.configure(state="disabled")
    def copy_output(self):
        if self.output_text and self.root:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.output_text.get("1.0", "end").strip())
    def save_output(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.output_text.get("1.0", "end"))
    def export_history(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"history": []}))
    def show_settings(self):
        pass
    def show_about(self):
        pass
    def undo(self):
        pass
    def redo(self):
        pass

def create_menu(root, input_text=None, output_text=None):
    """Create application menu and return the manager"""
    return MenuManager(root, input_text, output_text)

def sanitize_output(text):
    """Sanitize and clean up the model output"""
    if not text:
        return ""
    text = text.replace("```", "").replace("**", "")
    text = text.replace("#", "").replace("`", "")
    if "PRESENT TO USER:" in text:
        text = text.split("PRESENT TO USER:")[0]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines).strip()

class OutputHandler:
    """Handles output text updates safely"""
    @staticmethod
    def update(text, is_error=False):
        if app_state.output_text:
            app_state.output_text.configure(state="normal")
            app_state.output_text.delete("1.0", "end")
            app_state.output_text.insert("end", text)
            app_state.output_text.configure(state="disabled")

def update_output(text, is_error=False):
    """Updates the output text area."""
    try:
        OutputHandler.update(text, is_error)
    except Exception as e:
        logger.error(f"Failed to update output: {e}")

def handle_phase_error(phase_name, error, progress_tracker, loading, current_output):
    error_msg = f"\nError in {phase_name} phase: {str(error)}\n"
    logger.error(f"{phase_name} phase error: {error}")
    if current_output:
        update_output(current_output + error_msg, is_error=True)
    else:
        update_output(error_msg, is_error=True)
    loading.stop()
    return error_msg

def reset_ui_state():
    """Reset UI state after processing."""
    if app_state.status_bar:
        app_state.status_bar.set_status("Ready")
    if app_state.loading:
        app_state.loading.stop()
    if app_state.root:
        app_state.root.update()

def clear_output(output_text):
    output_text.configure(state="normal")
    output_text.delete("1.0", "end")
    output_text.configure(state="disabled")

def copy_to_clipboard(output_text):
    app_state.root.clipboard_clear()
    app_state.root.clipboard_append(output_text.get("1.0", "end").strip())
    
def save_output(output_text):
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(output_text.get("1.0", "end"))
    
def export_history():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"history": []}))

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
        if app_state.loading:
            app_state.loading.stop()
        if app_state.status_bar:
            app_state.status_bar.set_status("Application error", is_error=True)
        raise