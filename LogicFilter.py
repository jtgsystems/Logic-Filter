import customtkinter as ctk
import logging
from rich.logging import RichHandler
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkthemes import ThemedStyle
import json
from datetime import datetime
import requests
import sys
import os
import psutil
import threading
import asyncio

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
        
    def initialize(self, root):
        """Initialize application state with root window"""
        self.root = root
        from SettingsManager import SettingsManager
        self.settings_manager = SettingsManager()
        self.processing_history = ProcessingHistory()
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

# Create global application state
app_state = ApplicationState()

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

class OllamaServiceManager:
    def __init__(self, app_state):
        self.app_state = app_state
        self.ollama_ready = False
        self.models_loaded = False
        self.ollama_module = None
        self._start_service_check()
        
    def _start_service_check(self):
        """Start periodic service checking"""
        if self.app_state.root:
            self.app_state.root.after(1000, self.check_service_status)
        
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
                    import ollama
                    self.ollama_module = ollama
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
        """Periodically check Ollama service status"""
        if not self.ollama_ready:
            if self.initialize_ollama():
                if self.app_state.status_bar:
                    self.app_state.status_bar.set_status("Ollama connected")
            
        # Schedule next check only if not ready
        if not self.ollama_ready and self.app_state.root:
            self.app_state.root.after(5000, self.check_service_status)

    def chat(self, *args, **kwargs):
        """Wrapper for ollama.chat that ensures service is initialized"""
        if not self.ollama_ready:
            if not self.initialize_ollama():
                raise OllamaError("Ollama service not ready")
        return self.ollama_module.chat(*args, **kwargs)

# Create OllamaError class before it's used
class OllamaError(Exception):
    """Custom exception for Ollama-related errors."""
    pass

# Create global application state
app_state = ApplicationState()
ollama_manager = OllamaServiceManager(app_state)

# Configure TTK theme
def configure_ttk_style():
    style = ThemedStyle()
    style.set_theme("equilux")  # Dark theme that matches customtkinter
    return style

# Set customtkinter appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Configuration
OLLAMA_MODELS = {
    "analysis": "llama3.2:latest",  # Initial deep analysis
    "generation": "olmo2:13b",  # Creative solution generation
    "vetting": "deepseek-r1",  # Initial vetting
    "finalization": "deepseek-r1:14b",  # First round improvement
    "enhancement": "phi4:latest",  # Advanced enhancement
    "comprehensive": "phi4:latest",  # Initial comprehensive review
    "presenter": "deepseek-r1:14b",  # Final presentation cleanup
}

# Fallback model configuration
FALLBACK_ORDER = {
    "llama3.2:latest": ["deepseek-r1", "phi4:latest"],
    "olmo2:13b": ["deepseek-r1:14b", "phi4:latest"],
    "deepseek-r1": ["phi4:latest", "llama3.2:latest"],
    "deepseek-r1:14b": ["phi4:latest", "deepseek-r1"],
    "phi4:latest": ["deepseek-r1:14b", "llama3.2:latest"],
}

# Progress messages
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

# Global variables for UI elements
root = None
input_text = None
output_text = None
status_bar = None
loading = None
processing_history = None

def verify_model_availability(model_name):
    """Verify if an Ollama model is available."""
    try:
        if not app_state.ollama_manager.ollama_ready:
            return False
            
        # Try to ping the model with a timeout
        app_state.ollama_manager.chat(
            model=model_name, 
            messages=[{"role": "user", "content": "test"}],
            options={"timeout": 5000}  # 5 second timeout
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
        return []  # Don't validate if service isn't ready
        
    unavailable_models = []
    connection_error = None
    
    for purpose, model in OLLAMA_MODELS.items():
        try:
            if not verify_model_availability(model):
                unavailable_models.append((purpose, model))
        except OllamaError as e:
            if "Cannot connect" in str(e):
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
                ),
            }
        ]
        response = ollama_manager.chat(model=model_name, messages=messages)
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
        response = ollama_manager.chat(model=model_name, messages=messages)
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
                ),
            }
        ]
        response = ollama_manager.chat(model=model_name, messages=messages)
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
                    "Important: Stay focused on the original task. Return "
                    "only the improved version of the input prompt."
                ),
            }
        ]
        response = ollama_manager.chat(model_name, messages=messages)
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
                ),
            }
        ]
        response = ollama_manager.chat(model=model_name, messages=messages)
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
    model_name,
):
    """Creates final version and ensures clean presentation."""
    try:
        # First, use phi4 for comprehensive review
        messages = [
            {
                "role": "user",
                "content": (
                    "Review all versions of this prompt and create an "
                    "improved version that combines the best elements:\n\n"
                    f"Original: {original_prompt}\n"
                    f"Analysis: {analysis_report}\n"
                    f"Solutions: {solutions}\n"
                    f"Vetting: {vetting_report}\n"
                    f"Final: {final_prompt}\n"
                    f"Enhanced: {enhanced_prompt}\n\n"
                    "Create a refined version that maintains the core "
                    "intent while maximizing clarity and effectiveness."
                ),
            }
        ]
        response = ollama_manager.chat(model_name, messages=messages)
        improved = response["message"]["content"]

        # Then use deepseek-r1:14b as final presenter
        messages = [
            {
                "role": "user",
                "content": (
                    "You are the final presenter. Review this prompt and "
                    "ensure it's presented in the cleanest possible "
                    "format:\n\n{improved}\n\n"
                    "Requirements:\n"
                    "1. Remove any markdown formatting (**, #, etc)\n"
                    "2. Remove any meta-commentary or notes\n"
                    "3. Remove any section headers or labels\n"
                    "4. Present as clean, flowing paragraphs\n"
                    "5. Maintain all important content\n\n"
                    "First, identify 25 potential formatting or "
                    "presentation issues, then fix them all. Finally, "
                    "present the result in the cleanest possible format.\n\n"
                    "Start your response with 'PRESENT TO USER:' followed "
                    "by the final, clean prompt."
                ),
            }
        ]
        response = ollama_manager.chat(model=OLLAMA_MODELS["presenter"], messages=messages)
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during comprehensive review: {e}")
        raise OllamaError(f"Comprehensive review failed: {str(e)}")


def create_model_indicators(parent):
    """Creates a frame with model status indicators."""
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="x", pady=(0, 10))

    indicators = {}
    for model_type in OLLAMA_MODELS:
        label = ctk.CTkLabel(
            frame,
            text=f"● {model_type}",
            font=("Arial", 12),
            text_color="gray",
        )
        label.pack(side="left", padx=5)
        indicators[model_type] = label

    # Store indicators in app_state
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
        font=("Arial", 12),
    )

    if readonly:
        text_widget.configure(state="disabled")

    text_widget.pack(fill="both", expand=True)

    return frame, text_widget

def retry_with_fallback(func, *args, max_retries=3, fallback_model=None):
    """Retry a function with fallback model if available."""
    last_error = None
    current_model = args[-1]  # Last arg is always the model name
    
    # Try with primary model
    for attempt in range(max_retries):
        try:
            return func(*args)
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} with {current_model} failed: {str(e)}")
    
    # Try fallback models in order
    if current_model in FALLBACK_ORDER:
        for fallback in FALLBACK_ORDER[current_model]:
            try:
                logger.info(f"Attempting with fallback model {fallback}")
                new_args = list(args[:-1])
                new_args.append(fallback)
                return func(*new_args)
            except Exception as fallback_error:
                last_error = fallback_error
                logger.warning(f"Fallback attempt with {fallback} failed: {str(fallback_error)}")
    
    raise OllamaError(f"Operation failed after all attempts: {str(last_error)}")

class ProgressTracker:
    """Tracks progress through the enhancement pipeline."""
    def __init__(self, total_steps=6):
        self.total_steps = total_steps
        self.current_step = 0
        self.steps_completed = set()
        
    def update(self, step_name):
        """Update progress for a step."""
        if step_name not in self.steps_completed:
            self.current_step += 1
            self.steps_completed.add(step_name)
        
    def get_progress(self):
        """Get current progress as percentage."""
        return (self.current_step / self.total_steps) * 100

class LoadingIndicator:
    """Animated loading indicator."""
    def __init__(self, parent):
        self.parent = parent
        self.frame = ctk.CTkFrame(self.parent)
        self.progress = ctk.CTkProgressBar(self.frame)
        self.progress.set(0)  # Initialize progress to 0
        self.progress.pack(pady=10, padx=20, fill="x")
        self.label = ctk.CTkLabel(self.frame, text="Processing...")
        self.label.pack(pady=5)
        self.frame.pack_forget()
        
    def start(self, progress=0):
        """Start or update the loading animation."""
        self.progress.set(progress / 100)
        self.frame.pack(fill="x", pady=10)
        self.parent.update()
        
    def stop(self):
        """Stop the loading animation."""
        self.frame.pack_forget()
        self.parent.update()
        
    def update_label(self, text):
        """Update the loading indicator label."""
        self.label.configure(text=text)
        self.parent.update()

class ThemeManager:
    """Manages application themes."""
    THEMES = ["dark", "light", "system"]
    
    @staticmethod
    def toggle_theme():
        current = ctk.get_appearance_mode().lower()
        idx = (ThemeManager.THEMES.index(current) + 1) % len(ThemeManager.THEMES)
        new_theme = ThemeManager.THEMES[idx]
        ctk.set_appearance_mode(new_theme)
        return new_theme

class StatusBar(ctk.CTkFrame):
    """Enhanced status bar with multiple indicators"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setup_indicators()
        
    def setup_indicators(self):
        # Theme toggle
        self.theme_btn = ctk.CTkButton(
            self,
            text=f"Theme: {ctk.get_appearance_mode()}",
            command=self.toggle_theme,
            width=120,
            height=28
        )
        self.theme_btn.pack(side="left", padx=5, pady=5)
        
        # Model status
        self.model_status = ctk.CTkLabel(
            self,
            text="Models: Ready",
            text_color="gray"
        )
        self.model_status.pack(side="left", padx=20)
        
        # Processing status
        self.status = ctk.CTkLabel(
            self,
            text="Ready",
            text_color="gray"
        )
        self.status.pack(side="right", padx=5, pady=5)
        
        # Memory usage
        self.memory_label = ctk.CTkLabel(
            self,
            text="Memory: 0MB",
            text_color="gray"
        )
        self.memory_label.pack(side="right", padx=20)
        
        # Start memory monitoring
        self.update_memory_usage()
        
    def toggle_theme(self):
        current = ctk.get_appearance_mode().lower()
        new_theme = ThemeManager.toggle_theme()
        self.theme_btn.configure(text=f"Theme: {new_theme}")
        
    def update_memory_usage(self):
        """Update memory usage indicator"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_label.configure(text=f"Memory: {memory_mb:.1f}MB")
        self.after(5000, self.update_memory_usage)  # Update every 5 seconds
        
    def set_model_status(self, status, is_error=False):
        """Update model status indicator"""
        self.model_status.configure(
            text=f"Models: {status}",
            text_color="red" if is_error else "gray"
        )
        
    def set_status(self, text, is_error=False):
        """Update main status indicator"""
        self.status.configure(
            text=text,
            text_color="red" if is_error else "gray"
        )

def create_status_bar(parent):
    """Create status bar with theme toggle and connection status."""
    status_bar = StatusBar(parent)
    status_bar.pack(fill="x", side="bottom", pady=(5,0))
    return status_bar

class Toolbar(ctk.CTkFrame):
    """Enhanced toolbar with updatable references"""
    def __init__(self, parent, input_text=None, output_text=None):
        super().__init__(parent)
        self.input_text = input_text
        self.output_text = output_text
        self.setup_ui()
        self.pack(fill="x", pady=(0, 10))
        
    def setup_ui(self):
        buttons = [
            ("New (Ctrl+N)", self.new_document, "⌘"),
            ("Clear Output (Ctrl+L)", self.clear_output, "⌫"),
            ("Copy Output (Ctrl+Shift+C)", self.copy_output, "©"),
            ("Save Output (Ctrl+S)", self.save_output, "💾"),
            ("Export History (Ctrl+E)", self.export_history, "📋")
        ]
        
        for text, command, icon in buttons:
            btn = ctk.CTkButton(
                self,
                text=f"{icon} {text}",
                command=command,
                width=120,
                height=32
            )
            btn.pack(side="left", padx=5)
            
    def update_references(self, input_text, output_text):
        """Update text widget references"""
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
        if self.output_text:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.output_text.get("1.0", "end"))
                    
    def export_history(self):
        if app_state.processing_history:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(app_state.processing_history.history, f, indent=2)

def create_toolbar(parent):
    """Create toolbar with common actions."""
    return Toolbar(parent)  # Let the class handle the references later

class MenuManager:
    """Manages application menus and keyboard shortcuts"""
    def __init__(self, root, input_text=None, output_text=None):
        self.root = root
        self.input_text = input_text
        self.output_text = output_text
        self.create_menu()
        self.bind_shortcuts()
        
    def update_references(self, input_text, output_text):
        """Update text widget references"""
        self.input_text = input_text
        self.output_text = output_text
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="New (Ctrl+N)", command=self.new_document)
        file_menu.add_command(label="Clear Output (Ctrl+L)", command=self.clear_output)
        file_menu.add_command(label="Copy Output (Ctrl+Shift+C)", command=self.copy_output)
        file_menu.add_command(label="Save Output (Ctrl+S)", command=self.save_output)
        file_menu.add_command(label="Export History (Ctrl+E)", command=self.export_history)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        edit_menu.add_command(label="Undo (Ctrl+Z)", command=self.undo)
        edit_menu.add_command(label="Redo (Ctrl+Y)", command=self.redo)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_document())
        self.root.bind("<Control-l>", lambda e: self.clear_output())
        self.root.bind("<Control-Shift-KeyPress-C>", lambda e: self.copy_output())
        self.root.bind("<Control-s>", lambda e: self.save_output())
        self.root.bind("<Control-e>", lambda e: self.export_history())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        
    def new_document(self):
        if self.input_text:
            self.input_text.delete("1.0", "end")
            
    def clear_output(self):
        if self.output_text:
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.configure(state="disabled")
            
    def copy_output(self):
        if self.output_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.output_text.get("1.0", "end").strip())
            
    def save_output(self):
        if self.output_text:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.output_text.get("1.0", "end"))
                    
    def export_history(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(processing_history.history, f, indent=2)
                    
    def show_settings(self):
        SettingsDialog(self.root, app_state)
        
    def show_about(self):
        messagebox.showinfo(
            "About Prompt Enhancer",
            "Prompt Enhancer v1.0\n\n"
            "A tool for analyzing and improving prompts using multiple LLM models.\n\n"
            "Created with ❤️ using Python and CustomTkinter."
        )
        
    def undo(self):
        if processing_history and processing_history.can_undo():
            entry = processing_history.undo()
            if entry and self.input_text and self.output_text:
                self.input_text.delete("1.0", "end")
                self.input_text.insert("1.0", entry['input'])
                self.output_text.configure(state="normal")
                self.output_text.delete("1.0", "end")
                self.output_text.insert("1.0", entry['output'])
                self.output_text.configure(state="disabled")
                
    def redo(self):
        if processing_history and processing_history.can_redo():
            entry = processing_history.redo()
            if entry and self.input_text and self.output_text:
                self.input_text.delete("1.0", "end")
                self.input_text.insert("1.0", entry['input'])
                self.output_text.configure(state="normal")
                self.output_text.delete("1.0", "end")
                self.output_text.insert("1.0", entry['output'])
                self.output_text.configure(state="disabled")

def create_menu(root, input_text=None, output_text=None):
    """Create application menu and return the manager"""
    return MenuManager(root, input_text, output_text)

def sanitize_output(text):
    """Sanitize and clean up the model output."""
    if not text:
        return ""
        
    # Remove common formatting artifacts
    text = text.replace("```", "").replace("**", "").replace("#", "")
    
    # Remove any meta instructions that might have leaked through
    if "PRESENT TO USER:" in text:
        text = text.split("PRESENT TO USER:", 1)[1]
        
    # Clean up excessive newlines
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    
    return text.strip()

class OllamaError(Exception):
    """Custom exception for Ollama-related errors."""
    pass

class OutputHandler:
    """Handles output text updates safely"""
    @staticmethod
    def update(text_widget, text, is_error=False):
        try:
            text_widget.configure(state="normal")
            text_widget.delete("1.0", "end")
            text_widget.insert("end", text)
            text_widget.configure(state="disabled")
            text_widget.see("end")
            if is_error:
                text_widget.tag_add("error", "1.0", "end")
                text_widget.tag_configure("error", foreground="red")
        except Exception as e:
            logger.error(f"Failed to update output: {e}")

def update_output(text, is_error=False):
    """Updates the output text area."""
    try:
        text = sanitize_output(text)
        OutputHandler.update(app_state.output_text, text, is_error)
        app_state.status_bar.set_status(
            "Error" if is_error else "Ready",
            is_error=is_error
        )
        logger.info(text.strip())
    except Exception as e:
        logger.error(f"Failed to update output: {e}")
        if app_state.status_bar:
            app_state.status_bar.set_status("Error updating output", is_error=True)

def handle_phase_error(phase_name, error, progress_tracker, loading, current_output):
    """Handle errors during any processing phase."""
    error_msg = f"Error during {phase_name}: {str(error)}"
    logger.error(error_msg)
    
    # Check if we can continue with fallback
    if isinstance(error, OllamaError) and "Cannot connect" in str(error):
        return f"Error: Cannot connect to Ollama service. Please ensure Ollama is running.\n\n"
    
    # For other errors, try to provide helpful context
    if phase_name == "analysis":
        return f"Error: Initial analysis failed - {str(error)}\nPlease try again or enter a simpler prompt.\n\n"
    elif "timeout" in str(error).lower():
        return f"Error: {phase_name} timed out. The model may be busy, please try again.\n\n"
    
    # Generic error with recovery suggestion
    return f"Error in {phase_name}: {str(error)}\nPartial results preserved:\n\n{current_output}\n"

def reset_ui_state():
    """Reset UI state after processing."""
    app_state.status_bar.set_status("Ready")
    app_state.loading.stop()
    reset_indicators()  # Reset all model indicators
    app_state.root.update()

def create_toolbar(parent, input_text, output_text):
    """Create toolbar with common actions."""
    toolbar = ctk.CTkFrame(parent)
    toolbar.pack(fill="x", pady=(0, 10))
    
    buttons = [
        ("New (Ctrl+N)", lambda: input_text.delete("1.0", "end"), "⌘"),
        ("Clear Output (Ctrl+L)", lambda: clear_output(output_text), "⌫"),
        ("Copy Output (Ctrl+Shift+C)", lambda: copy_to_clipboard(output_text), "©"),
        ("Save Output (Ctrl+S)", lambda: save_output(output_text), "💾"),
        ("Export History (Ctrl+E)", lambda: export_history(), "📋")
    ]
    
    for text, command, icon in buttons:
        btn = ctk.CTkButton(
            toolbar,
            text=f"{icon} {text}",
            command=command,
            width=120,
            height=32
        )
        btn.pack(side="left", padx=5)
    
    return toolbar

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
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(output_text.get("1.0", "end"))
            
def export_history():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(app_state.processing_history, f, indent=2)

class ProcessingHistory:
    """Manages processing history and undo/redo functionality."""
    def __init__(self):
        self.history = []
        self.current_index = -1
        self.max_history = 50
        
    def add(self, input_text, output_text):
        """Add a new processing result to history."""
        entry = {
            'input': input_text,
            'output': output_text,
            'timestamp': datetime.now().isoformat()
        }
        
        # Remove any redo entries
        self.history = self.history[:self.current_index + 1]
        self.history.append(entry)
        self.current_index += 1
        
        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.current_index = len(self.history) - 1
            
    def can_undo(self):
        return self.current_index > 0
        
    def can_redo(self):
        return self.current_index < len(self.history) - 1
        
    def undo(self):
        """Get previous processing result."""
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index]
        return None
        
    def redo(self):
        """Get next processing result."""
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index]
        return None

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
            'default_models': OLLAMA_MODELS.copy(),
            'window': {
                'geometry': '1024x768',
                'zoomed': False
            }
        }
        self.settings = self.load_settings()
        
    def load_settings(self):
        """Load settings from file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all settings exist
                    return {**self.default_settings, **loaded}
            return self.default_settings.copy()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return self.default_settings.copy()
            
    def save_settings(self):
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            
    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
        
    def set(self, key, value):
        """Set a setting value."""
        try:
            self.settings[key] = value
            if self.get('autosave', True):
                self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set setting {key}: {e}")

    def update_window_state(self, geometry, zoomed):
        """Update window state settings."""
        self.settings['window'] = {
            'geometry': geometry,
            'zoomed': zoomed
        }
        if self.get('autosave', True):
            self.save_settings()

class SettingsDialog:
    """Dialog for editing application settings."""
    def __init__(self, parent, app_state):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Settings")
        self.window.geometry("600x400")
        self.app_state = app_state
        
        # Make modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the dialog
        self.center_window()
        
        self.create_widgets()
        
    def center_window(self):
        """Center the dialog on the parent window."""
        self.window.update_idletasks()
        parent = self.window.master
        x = parent.winfo_x() + (parent.winfo_width() - self.window.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        # Create scrollable frame for settings
        container = ctk.CTkScrollableFrame(self.window)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Theme selection
        theme_frame = ctk.CTkFrame(container)
        theme_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=5)
        theme_var = ctk.StringVar(value=self.app_state.settings_manager.get('theme'))
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["dark", "light", "system"],
            variable=theme_var,
            command=self.on_theme_change
        )
        theme_menu.pack(side="left", padx=5)
        
        # Font size
        font_frame = ctk.CTkFrame(container)
        font_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(font_frame, text="Font Size:").pack(side="left", padx=5)
        self.font_size_label = ctk.CTkLabel(font_frame, text=str(self.app_state.settings_manager.get('font_size')))
        self.font_size_label.pack(side="right", padx=5)
        
        font_size = ctk.CTkSlider(
            font_frame,
            from_=8,
            to=24,
            number_of_steps=16,
            command=self.on_font_size_change
        )
        font_size.set(self.app_state.settings_manager.get('font_size'))
        font_size.pack(side="left", padx=5, expand=True, fill="x")
        
        # Checkboxes for boolean settings
        checks_frame = ctk.CTkFrame(container)
        checks_frame.pack(fill="x", pady=10)
        
        self.checkboxes = {}
        for setting, label in [
            ('autosave', "Auto-save settings"),
            ('show_model_indicators', "Show model indicators"),
            ('save_window_state', "Remember window position")
        ]:
            var = tk.BooleanVar(value=self.app_state.settings_manager.get(setting))
            cb = ctk.CTkCheckBox(
                checks_frame,
                text=label,
                variable=var,
                command=lambda s=setting, v=var: self.on_checkbox_change(s, v)
            )
            cb.pack(anchor="w", padx=5, pady=2)
            self.checkboxes[setting] = (cb, var)
            
        # Status bar
        self.status_label = ctk.CTkLabel(
            self.window,
            text="",
            text_color="gray"
        )
        self.status_label.pack(side="bottom", pady=5)
            
        # Buttons frame
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        
        # Save button
        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self.save_settings
        ).pack(side="left", padx=5)
        
        # Close button
        ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.window.destroy
        ).pack(side="right", padx=5)
        
    def on_theme_change(self, theme):
        """Handle theme change"""
        try:
            self.app_state.settings_manager.set('theme', theme)
            ctk.set_appearance_mode(theme)
            self.show_status("Theme updated")
        except Exception as e:
            self.show_status(f"Failed to update theme: {e}", is_error=True)
            
    def on_font_size_change(self, value):
        """Handle font size change"""
        try:
            size = int(value)
            self.app_state.settings_manager.set('font_size', size)
            self.font_size_label.configure(text=str(size))
            self.update_font_size(size)
            self.show_status("Font size updated")
        except Exception as e:
            self.show_status(f"Failed to update font size: {e}", is_error=True)
            
    def on_checkbox_change(self, setting, var):
        """Handle checkbox changes"""
        try:
            value = var.get()
            self.app_state.settings_manager.set(setting, value)
            self.show_status(f"{setting} updated")
        except Exception as e:
            self.show_status(f"Failed to update {setting}: {e}", is_error=True)
            
    def update_font_size(self, size):
        """Update font size for text widgets"""
        try:
            if self.app_state.input_text:
                self.app_state.input_text.configure(font=("Arial", size))
            if self.app_state.output_text:
                self.app_state.output_text.configure(font=("Arial", size))
        except Exception as e:
            self.show_status(f"Failed to apply font size: {e}", is_error=True)
            
    def save_settings(self):
        """Save all settings"""
        try:
            self.app_state.settings_manager.save_settings()
            self.show_status("Settings saved successfully")
        except Exception as e:
            self.show_status(f"Failed to save settings: {e}", is_error=True)
            
    def show_status(self, message, is_error=False):
        """Show status message"""
        self.status_label.configure(
            text=message,
            text_color="red" if is_error else "gray"
        )

class InputPane(ctk.CTkFrame):
    """Enhanced input pane with additional features"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setup_ui()
        
    def setup_ui(self):
        # Template selector
        template_frame = ctk.CTkFrame(self)
        template_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            template_frame,
            text="Template:",
            font=("Arial", 12)
        ).pack(side="left", padx=5)
        
        self.template_var = ctk.StringVar(value="None")
        template_menu = ctk.CTkOptionMenu(
            template_frame,
            values=["None", "Analysis", "Story", "Code Review", "Bug Report"],
            variable=self.template_var,
            command=self.load_template,
            width=150
        )
        template_menu.pack(side="left", padx=5)
        
        # Character counter
        self.char_count = ctk.CTkLabel(
            template_frame,
            text="Characters: 0",
            font=("Arial", 12)
        )
        self.char_count.pack(side="right", padx=10)
        
        # Input area with line numbers
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(fill="both", expand=True)
        
        self.line_numbers = ctk.CTkTextbox(
            self.input_frame,
            width=40,
            font=("Arial", 12),
            fg_color="gray20",
            border_width=0
        )
        self.line_numbers.pack(side="left", fill="y")
        
        self.text = ctk.CTkTextbox(
            self.input_frame,
            font=("Arial", 12),
            wrap="word"
        )
        self.text.pack(side="left", fill="both", expand=True)
        
        # Bind events
        self.text.bind("<<Modified>>", self.on_text_change)
        self.text.bind("<Key>", self.update_line_numbers)
        
    def on_text_change(self, event=None):
        """Handle text changes"""
        content = self.text.get("1.0", "end-1c")
        char_count = len(content)
        self.char_count.configure(text=f"Characters: {char_count}")
        self.update_line_numbers()
        self.text.edit_modified(False)
        
    def update_line_numbers(self, event=None):
        """Update line numbers display"""
        content = self.text.get("1.0", "end-1c")
        lines = content.count("\n") + 1
        line_numbers = "\n".join(str(i) for i in range(1, lines + 1))
        
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", line_numbers)
        self.line_numbers.configure(state="disabled")
        
    def load_template(self, template_name):
        """Load selected template"""
        templates = {
            "Analysis": "Please analyze the following:\n\n",
            "Story": "Write a story about:\n\n",
            "Code Review": "Please review this code:\n\n",
            "Bug Report": "Bug Description:\n\nSteps to Reproduce:\n\nExpected Result:\n\nActual Result:\n"
        }
        
        if template_name != "None":
            self.text.delete("1.0", "end")
            self.text.insert("1.0", templates.get(template_name, ""))

class OutputPane(ctk.CTkFrame):
    """Enhanced output pane with additional features"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setup_ui()
        
    def setup_ui(self):
        # Output controls
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Format selector
        ctk.CTkLabel(
            control_frame,
            text="Format:",
            font=("Arial", 12)
        ).pack(side="left", padx=5)
        
        self.format_var = ctk.StringVar(value="Plain Text")
        format_menu = ctk.CTkOptionMenu(
            control_frame,
            values=["Plain Text", "Markdown", "Code", "JSON"],
            variable=self.format_var,
            command=self.format_output,
            width=120
        )
        format_menu.pack(side="left", padx=5)
        
        # Word/char count
        self.count_label = ctk.CTkLabel(
            control_frame,
            text="Words: 0 | Characters: 0",
            font=("Arial", 12)
        )
        self.count_label.pack(side="right", padx=10)
        
        # Search bar
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", pady=(0, 10))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search in output...",
            width=200
        )
        self.search_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(
            search_frame,
            text="Find",
            width=60,
            command=self.find_text
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            search_frame,
            text="Previous",
            width=80,
            command=lambda: self.find_text(backwards=True)
        ).pack(side="left", padx=5)
        
        # Output area
        self.text = ctk.CTkTextbox(
            self,
            font=("Arial", 12),
            wrap="word",
            state="disabled"
        )
        self.text.pack(fill="both", expand=True)
        
        # Bind events
        self.search_entry.bind("<Return>", lambda e: self.find_text())
        
    def format_output(self, format_type):
        """Format the output text based on selected format"""
        if self.text.get("1.0", "end-1c").strip():
            content = self.text.get("1.0", "end-1c")
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            
            if format_type == "Code":
                content = "```\n" + content + "\n```"
            elif format_type == "JSON":
                try:
                    parsed = json.loads(content)
                    content = json.dumps(parsed, indent=2)
                except:
                    pass
                    
            self.text.insert("1.0", content)
            self.text.configure(state="disabled")
            self.update_counts()
            
    def update_counts(self):
        """Update word and character counts"""
        content = self.text.get("1.0", "end-1c")
        words = len(content.split())
        chars = len(content)
        self.count_label.configure(
            text=f"Words: {words} | Characters: {chars}"
        )
        
    def find_text(self, backwards=False):
        """Search for text in output"""
        search_text = self.search_entry.get()
        if not search_text:
            return
            
        content = self.text.get("1.0", "end-1c")
        current_pos = self.text.index("insert")
        
        if backwards:
            search_pos = self.text.search(
                search_text,
                current_pos,
                backwards=True,
                stopindex="1.0"
            )
        else:
            search_pos = self.text.search(
                search_text,
                current_pos,
                stopindex="end"
            )
            
        if search_pos:
            line, char = map(int, search_pos.split('.'))
            self.text.tag_remove("search", "1.0", "end")
            self.text.tag_add(
                "search",
                search_pos,
                f"{line}.{char + len(search_text)}"
            )
            self.text.tag_configure("search", background="yellow")
            self.text.see(search_pos)
            self.text.mark_set("insert", search_pos)
        else:
            # Start from beginning if not found
            if not backwards:
                self.text.mark_set("insert", "1.0")
                self.find_text()

def process_prompt():
    """Process the input prompt through the enhancement pipeline."""
    # First check if Ollama is ready
    if not app_state.ollama_manager.ollama_ready:
        if not app_state.ollama_manager.initialize_ollama():
            app_state.status_bar.set_status("Ollama service not ready", is_error=True)
            messagebox.showwarning(
                "Service Not Ready",
                "The Ollama service is not running. Please start Ollama and try again.\n\n"
                "If Ollama is not installed, visit: https://ollama.com/download"
            )
            return

    try:
        app_state.status_bar.set_status("Checking models...")
        app_state.loading.start(0)
        
        # Validate models before starting
        unavailable_models = validate_models()
        if unavailable_models:
            error_msg = "Some models are not available. Using fallback models where possible.\n"
            for purpose, model in unavailable_models:
                if model in FALLBACK_ORDER:
                    fallbacks = ", ".join(FALLBACK_ORDER[model])
                    error_msg += f"- {purpose}: {model} (fallbacks: {fallbacks})\n"
                else:
                    error_msg += f"- {purpose}: {model} (no fallbacks available)\n"
            logger.warning(error_msg)
            
            # Show warning to user
            messagebox.showwarning(
                "Model Availability",
                "Some models are not available. The application will use fallback models.\n\n"
                "This may affect the quality of results."
            )

        initial_prompt = app_state.input_text.get("1.0", "end").strip()
        if not initial_prompt:
            update_output("Error: No prompt entered.", is_error=True)
            app_state.loading.stop()
            return

        app_state.status_bar.set_status("Processing...")
        progress = ProgressTracker()
        app_state.loading.start(0)
        
        initial_prompt = app_state.input_text.get("1.0", "end").strip()
        if not initial_prompt:
            update_output("Error: No prompt entered.", is_error=True)
            app_state.loading.stop()
            return

        output = PROGRESS_MESSAGES["start"]
        update_output(output)

        # Store results between phases
        results = {}

        # Process through each phase
        phases = [
            ("Analysis", "analyzing", analyze_prompt, "analysis", [lambda: initial_prompt]),
            ("Generation", "generating", generate_solutions, "generation", [lambda: results["Analysis"]]),
            ("Vetting", "vetting", vet_and_refine, "vetting", [lambda: results["Generation"]]),
            ("Finalization", "finalizing", finalize_prompt, "finalization", [lambda: results["Vetting"], lambda: initial_prompt]),
            ("Enhancement", "enhancing", enhance_prompt, "enhancement", [lambda: results["Finalization"]]),
            ("Review", "comprehensive", comprehensive_review, "comprehensive", [
                lambda: initial_prompt,
                lambda: results["Analysis"],
                lambda: results["Generation"],
                lambda: results["Vetting"],
                lambda: results["Finalization"],
                lambda: results["Enhancement"]
            ])
        ]

        for phase_name, msg_key, func, model_key, arg_providers in phases:
            app_state.status_bar.set_status(f"Running {phase_name}...")
            app_state.loading.update_label(f"Running {phase_name}...")
            output += PROGRESS_MESSAGES[msg_key]
            update_output(output)

            try:
                # Get arguments for this phase
                args = [provider() for provider in arg_providers]
                args.append(OLLAMA_MODELS[model_key])  # Add model name as last argument
                
                # Run the phase
                result = retry_with_fallback(func, *args)
                results[phase_name] = result

                progress.update(phase_name)
                output += PROGRESS_MESSAGES[msg_key.replace("ing", "_done")]
                output += result + "\n\n"
                update_output(output)
                app_state.loading.start(progress.get_progress())

            except Exception as e:
                error_msg = handle_phase_error(phase_name, e, progress, app_state.loading, output)
                update_output(output + error_msg, is_error=True)
                return

        # Add to history
        app_state.processing_history.add(initial_prompt, output)
        
    except Exception as e:
        logger.exception("Error during prompt processing")
        update_output(f"An error occurred: {str(e)}", is_error=True)
    finally:
        app_state.status_bar.set_status("Ready")
        app_state.loading.stop()
        app_state.root.update()

def main():
    """Main function."""
    try:
        # Ensure we're running in the main thread
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("GUI must be started in the main thread")
            
        # Configure ttk style first
        style = configure_ttk_style()
        
        # Initialize main window
        root = ctk.CTk()
        root.title("Prompt Enhancer")
        root.minsize(800, 600)
        root.geometry("1024x768")

        # Initialize application state
        app_state.initialize(root)
        
        # Force the window to update before continuing
        root.update_idletasks()
        
        # Create main container
        main_frame = ctk.CTkFrame(root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create model indicators
        model_indicators_frame = create_model_indicators(main_frame)
        
        # Create status bar
        status_bar = StatusBar(root)
        status_bar.pack(fill="x", side="bottom", pady=(5,0))
        app_state.update_references(status_bar=status_bar)

        # Create toolbar with initial None references
        toolbar = Toolbar(main_frame)
        app_state.update_references(toolbar=toolbar)

        # Create paned window for resizable sections
        paned_window = ttk.PanedWindow(main_frame, orient="vertical", style="Vertical.TPanedwindow")
        paned_window.pack(fill="both", expand=True, pady=(10, 0))

        # Create input pane
        input_pane = InputPane(paned_window)
        paned_window.add(input_pane, weight=1)
        
        # Create output pane
        output_pane = OutputPane(paned_window)
        paned_window.add(output_pane, weight=2)
        
        # Update references for input and output
        app_state.update_references(
            input_text=input_pane.text,
            output_text=output_pane.text
        )
        
        # Create loading indicator
        loading = LoadingIndicator(main_frame)
        app_state.update_references(loading=loading)

        # Create process button
        process_button = ctk.CTkButton(
            main_frame,
            text="Process & Improve Prompt",
            command=process_prompt,
            font=("Arial", 12),
            height=40,
        )
        process_button.pack(pady=10)

        # Create menu manager
        menu_manager = MenuManager(root)
        app_state.update_references(menu_manager=menu_manager)

        # Window state management
        def save_window_state(event=None):
            if root.winfo_exists():
                config = {
                    'geometry': root.geometry(),
                    'zoomed': root.state() == 'zoomed'
                }
                app_state.settings_manager.update_window_state(
                    config['geometry'],
                    config['zoomed']
                )

        # Load previous window state
        window_settings = app_state.settings_manager.get('window', {})
        if window_settings.get('zoomed'):
            root.state('zoomed')
        elif window_settings.get('geometry'):
            root.geometry(window_settings['geometry'])

        root.protocol("WM_DELETE_WINDOW", lambda: [save_window_state(), root.destroy()])

        # Set initial theme from settings
        ctk.set_appearance_mode(app_state.settings_manager.get('theme', 'dark'))

        # Final setup before mainloop
        root.update_idletasks()
        
        # Start the application
        root.mainloop()

    except Exception as e:
        logger.exception("Failed to initialize application")
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import threading  # Add threading import at the top
    main()
`
