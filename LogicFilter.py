import customtkinter as ctk
import logging
from rich.logging import RichHandler
import tkinter as tk
import json
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import requests
import sys

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("prompt_enhancer")

def check_ollama_service():
    """Check if Ollama service is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/health", timeout=5)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    return False

def ensure_ollama_running():
    """Ensure Ollama service is running before importing."""
    if not check_ollama_service():
        messagebox.showerror(
            "Ollama Service Not Found",
            "The Ollama service is not running. Please start Ollama and try again.\n\n"
            "If Ollama is not installed, visit: https://ollama.com/download"
        )
        sys.exit(1)

# Check Ollama service before importing
ensure_ollama_running()

# Now import ollama after confirming service is running
import ollama

# Set customtkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class OllamaError(Exception):
    """Custom exception for Ollama-related errors."""
    pass

def verify_model_availability(model_name):
    """Verify if an Ollama model is available."""
    try:
        # Try to ping the model with a timeout
        response = ollama.chat(
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
        response = ollama.chat(model=model_name, messages=messages)
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
        response = ollama.chat(model=model_name, messages=messages)
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
        response = ollama.chat(model=model_name, messages=messages)
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
        response = ollama.chat(model=model_name, messages=messages)
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
        response = ollama.chat(model=model_name, messages=messages)
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
        response = ollama.chat(model_name, messages=messages)
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
        response = ollama.chat(model=OLLAMA_MODELS["presenter"], messages=messages)
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

    return indicators


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
        self.frame = ctk.CTkFrame(parent)
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
        import psutil
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

def create_menu(root, input_text, output_text):
    """Create menu bar with keyboard shortcuts."""
    def clear_all():
        input_text.delete("1.0", "end")
        output_text.configure(state="normal")
        output_text.delete("1.0", "end")
        output_text.configure(state="disabled")

    def copy_output():
        root.clipboard_clear()
        root.clipboard_append(output_text.get("1.0", "end").strip())

    menubar = tk.Menu(root)
    root.config(menu=menubar)

    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Clear All (Ctrl+L)", command=clear_all)
    file_menu.add_command(label="Copy Output (Ctrl+Shift+C)", command=copy_output)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)

    # Bind keyboard shortcuts
    root.bind("<Control-l>", lambda e: clear_all())
    root.bind("<Control-Shift-KeyPress-C>", lambda e: copy_output())

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

def update_output(text):
    """Updates the output text area."""
    try:
        output_text.configure(state="normal")
        output_text.delete("1.0", "end")
        text = sanitize_output(text)
        output_text.insert("end", text)
        output_text.configure(state="disabled")
        output_text.see("end")
        status_bar.set_status("Ready")
        logger.info(text.strip())
    except Exception as e:
        logger.error(f"Failed to update output: {e}")
        status_bar.set_status("Error updating output", is_error=True)

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
    status_bar.set_status("Ready")
    loading.stop()
    reset_indicators()  # Reset all model indicators
    root.update()

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
    root.clipboard_clear()
    root.clipboard_append(output_text.get("1.0", "end").strip())
    
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
            json.dump(processing_history, f, indent=2)

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
        self.settings_file = 'settings.json'
        self.default_settings = {
            'theme': 'dark',
            'font_size': 12,
            'max_history': 50,
            'autosave': True,
            'show_model_indicators': True,
            'save_window_state': True,
            'default_models': OLLAMA_MODELS.copy()
        }
        self.settings = self.load_settings()
        
    def load_settings(self):
        """Load settings from file."""
        try:
            with open(self.settings_file, 'r') as f:
                return {**self.default_settings, **json.load(f)}
        except:
            return self.default_settings.copy()
            
    def save_settings(self):
        """Save current settings to file."""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
            
    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
        
    def set(self, key, value):
        """Set a setting value."""
        self.settings[key] = value
        if self.get('autosave', True):
            self.save_settings()
            
class SettingsDialog:
    """Dialog for editing application settings."""
    def __init__(self, parent, settings_manager):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Settings")
        self.window.geometry("600x400")
        self.settings = settings_manager
        
        # Make modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Theme selection
        theme_frame = ctk.CTkFrame(self.window)
        theme_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=5)
        theme_var = ctk.StringVar(value=self.settings.get('theme'))
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["dark", "light", "system"],
            variable=theme_var,
            command=lambda t: self.settings.set('theme', t)
        )
        theme_menu.pack(side="left", padx=5)
        
        # Font size
        font_frame = ctk.CTkFrame(self.window)
        font_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(font_frame, text="Font Size:").pack(side="left", padx=5)
        font_size = ctk.CTkSlider(
            font_frame,
            from_=8,
            to=24,
            number_of_steps=16,
            command=lambda v: self.settings.set('font_size', int(v))
        )
        font_size.set(self.settings.get('font_size'))
        font_size.pack(side="left", padx=5, expand=True, fill="x")
        
        # Checkboxes for boolean settings
        checks_frame = ctk.CTkFrame(self.window)
        checks_frame.pack(fill="x", padx=20, pady=10)
        
        for setting, label in [
            ('autosave', "Auto-save settings"),
            ('show_model_indicators', "Show model indicators"),
            ('save_window_state', "Remember window position")
        ]:
            var = tk.BooleanVar(value=self.settings.get(setting))
            cb = ctk.CTkCheckBox(
                checks_frame,
                text=label,
                variable=var,
                command=lambda s=setting, v=var: self.settings.set(s, v.get())
            )
            cb.pack(anchor="w", padx=5, pady=2)
            
        # Close button
        ctk.CTkButton(
            self.window,
            text="Close",
            command=self.window.destroy
        ).pack(side="bottom", pady=10)

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

def main():
    """Main function."""
    progress_msgs = PROGRESS_MESSAGES

    root = ctk.CTk()
    root.title("Prompt Enhancer")
    root.minsize(800, 600)
    root.geometry("1024x768")  # Set default size
    
    # Save window size and position on close
    def save_window_state(event=None):
        if root.winfo_exists():
            config = {
                'geometry': root.geometry(),
                'zoomed': root.state() == 'zoomed'
            }
            with open('window_state.json', 'w') as f:
                json.dump(config, f)
    
    # Load previous window state
    try:
        with open('window_state.json', 'r') as f:
            config = json.load(f)
            if config.get('zoomed'):
                root.state('zoomed')
            else:
                root.geometry(config['geometry'])
    except:
        pass  # Use default if no saved state
        
    root.protocol("WM_DELETE_WINDOW", lambda: [save_window_state(), root.destroy()])
    
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Create splitter frame for resizable panes
    paned_window = ttk.PanedWindow(main_frame, orient="vertical")
    paned_window.pack(fill="both", expand=True)

    # Create top pane for input
    input_pane = InputPane(paned_window)
    paned_window.add(input_pane, weight=1)

    # Create bottom pane for output
    output_pane = OutputPane(paned_window)
    paned_window.add(output_pane, weight=2)

    # Create model status indicators
    model_indicators = create_model_indicators(main_frame)

    # Reset all indicators to inactive
    def reset_indicators():
        for label in model_indicators.values():
            label.configure(text_color="gray")

    # Set an indicator as active
    def set_active_model(model_type):
        reset_indicators()
        model_indicators[model_type].configure(text_color="#4a90e2")

    input_label = ctk.CTkLabel(
        input_pane,
        text="Enter your prompt:",
        font=("Arial", 14, "bold"),
    )
    input_label.pack(anchor="w")

    input_frame, input_text = create_scrolled_text(
        input_pane,
        height=100,
        width=700,
    )
    input_frame.pack(fill="x", pady=(5, 15))

    output_label = ctk.CTkLabel(
        output_pane,
        text="Results:",
        font=("Arial", 14, "bold"),
    )
    output_label.pack(anchor="w")

    output_frame, output_text = create_scrolled_text(
        output_pane,
        height=400,
        width=700,
        readonly=True,
    )
    output_frame.pack(fill="both", expand=True, pady=(5, 15))

    # Add loading indicator after the input area
    loading = LoadingIndicator(main_frame)

    # Add status bar before mainloop
    status_bar = create_status_bar(main_frame)

    # Add toolbar
    create_toolbar(main_frame, input_text, output_text)

    def process_prompt():
        try:
            status_bar.set_status("Processing...")
            progress = ProgressTracker()
            loading.start(0)
            
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
                status_bar.set_model_status("Some models unavailable", is_error=True)

            initial_prompt = input_text.get("1.0", "end").strip()
            if not initial_prompt:
                update_output("Error: No prompt entered.")
                loading.stop()
                return

            output = progress_msgs["start"]
            update_output(output)

            # Phase 1: Analysis with retry
            logger.info("Starting analysis phase...")
            set_active_model("analysis")
            output += progress_msgs["analyzing"]
            loading.update_label("Analyzing prompt...")
            update_output(output)

            try:
                analysis_report = retry_with_fallback(
                    analyze_prompt,
                    initial_prompt,
                    OLLAMA_MODELS["analysis"]
                )
                progress.update("analysis")
            except OllamaError as e:
                error_output = handle_phase_error("analysis", e, progress, loading, output)
                update_output(error_output)
                reset_ui_state()
                return

            output += progress_msgs["analysis_done"]
            output += analysis_report + "\n\n"
            update_output(output)
            loading.start(progress.get_progress())

            # Phase 2: Solution Generation
            set_active_model("generation")
            output += progress_msgs["generating"]
            loading.update_label("Generating solutions...")
            update_output(output)

            try:
                solutions = retry_with_fallback(
                    generate_solutions,
                    analysis_report,
                    OLLAMA_MODELS["generation"]
                )
                progress.update("generation")
            except OllamaError as e:
                error_output = handle_phase_error("generation", e, progress, loading, output)
                update_output(error_output)
                reset_ui_state()
                return

            output += progress_msgs["generation_done"]
            output += solutions + "\n\n"
            update_output(output)
            loading.start(progress.get_progress())

            # Phase 3: Vetting
            set_active_model("vetting")
            output += progress_msgs["vetting"]
            loading.update_label("Vetting solutions...")
            update_output(output)

            try:
                vetting_report = retry_with_fallback(
                    vet_and_refine,
                    solutions,
                    OLLAMA_MODELS["vetting"]
                )
                progress.update("vetting")
            except OllamaError as e:
                error_output = handle_phase_error("vetting", e, progress, loading, output)
                update_output(error_output)
                reset_ui_state()
                return

            output += progress_msgs["vetting_done"]
            output += vetting_report + "\n\n"
            update_output(output)
            loading.start(progress.get_progress())

            # Phase 4: Initial Finalization
            set_active_model("finalization")
            output += progress_msgs["finalizing"]
            loading.update_label("Finalizing prompt...")
            update_output(output)

            try:
                final_result = retry_with_fallback(
                    finalize_prompt,
                    vetting_report,
                    initial_prompt,
                    OLLAMA_MODELS["finalization"]
                )
                progress.update("finalization")
            except OllamaError as e:
                error_output = handle_phase_error("finalization", e, progress, loading, output)
                update_output(error_output)
                reset_ui_state()
                return

            output += progress_msgs["finalize_done"]
            output += final_result + "\n\n"
            update_output(output)
            loading.start(progress.get_progress())

            # Phase 5: Enhancement
            set_active_model("enhancement")
            output += progress_msgs["enhancing"]
            loading.update_label("Enhancing prompt...")
            update_output(output)

            try:
                enhanced_result = retry_with_fallback(
                    enhance_prompt,
                    final_result,
                    OLLAMA_MODELS["enhancement"]
                )
                progress.update("enhancement")
            except OllamaError as e:
                error_output = handle_phase_error("enhancement", e, progress, loading, output)
                update_output(error_output)
                reset_ui_state()
                return

            output += progress_msgs["enhance_done"]
            output += enhanced_result + "\n\n"
            update_output(output)
            loading.start(progress.get_progress())

            # Phase 6: Comprehensive Review
            set_active_model("comprehensive")
            output += progress_msgs["comprehensive"]
            loading.update_label("Performing comprehensive review...")
            update_output(output)

            try:
                # First use comprehensive model
                comprehensive_result = retry_with_fallback(
                    comprehensive_review,
                    initial_prompt,
                    analysis_report,
                    solutions,
                    vetting_report,
                    final_result,
                    enhanced_result,
                    OLLAMA_MODELS["comprehensive"]
                )
                progress.update("comprehensive")
            except OllamaError as e:
                error_output = handle_phase_error("comprehensive", e, progress, loading, output)
                update_output(error_output)
                reset_ui_state()
                return

            # Final presentation cleanup
            set_active_model("presenter")
            loading.update_label("Cleaning up presentation...")
            output += "Cleaning up final presentation...\n"
            update_output(output)

            # Present final result
            output += progress_msgs["complete"]
            if "PRESENT TO USER:" in comprehensive_result:
                final_text = comprehensive_result.split("PRESENT TO USER:", 1)[1].strip()
                output += final_text + "\n"
            else:
                output += comprehensive_result + "\n"
            update_output(output)

        except Exception as e:
            logger.exception("Error during prompt processing")
            update_output(f"An error occurred: {str(e)}")
            return
        finally:
            status_bar.set_status("Ready")
            loading.stop()

    process_button = ctk.CTkButton(
        main_frame,
        text="Process & Improve Prompt",
        command=process_prompt,
        font=("Arial", 12),
        height=40,
    )
    process_button.pack(pady=10)

    # Add menu bar after root setup
    create_menu(root, input_text, output_text)

    root.mainloop()


if __name__ == "__main__":
    main()
