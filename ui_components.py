import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Union, Tuple
import logging
import json
import time
import psutil

logger = logging.getLogger("prompt_enhancer")

class LoadingIndicator:
    """Animated loading indicator with improved performance"""
    def __init__(self, parent):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent)
        self._progress_value = 0
        self._animation_after = None
        self._animation_speed = 50  # milliseconds per update
        
        self.progress = ctk.CTkProgressBar(self.frame)
        self.progress.set(0)
        self.progress.pack(pady=10, padx=20, fill="x")
        
        self.label = ctk.CTkLabel(self.frame, text="Processing...")
        self.label.pack(pady=5)
        
        self.frame.pack_forget()
        
    def start(self, progress=0):
        """Start or update the loading animation"""
        self._progress_value = progress / 100
        self.progress.set(self._progress_value)
        self.frame.pack(fill="x", pady=10)
        self._start_animation()
        self.parent.update_idletasks()
        
    def _start_animation(self):
        """Start the progress bar animation"""
        if self._animation_after:
            self.parent.after_cancel(self._animation_after)
            
        def animate():
            if not self.frame.winfo_ismapped():
                return
                
            # Add a small amount to progress for animation effect
            current = self.progress.get()
            target = min(self._progress_value + 0.1, 1.0)
            if current < target:
                self.progress.set(current + 0.01)
                self._animation_after = self.parent.after(self._animation_speed, animate)
            else:
                self.progress.set(self._progress_value)
                
        self._animation_after = self.parent.after(0, animate)
        
    def stop(self):
        """Stop the loading animation"""
        if self._animation_after:
            self.parent.after_cancel(self._animation_after)
            self._animation_after = None
        self.frame.pack_forget()
        self.parent.update_idletasks()
        
    def update_label(self, text):
        """Update the loading indicator label"""
        self.label.configure(text=text)
        self.parent.update_idletasks()
        
    def destroy(self):
        """Clean up resources"""
        if self._animation_after:
            self.parent.after_cancel(self._animation_after)
        self.frame.destroy()

class StatusBar(ctk.CTkFrame):
    """Enhanced status bar with multiple indicators"""
    def __init__(self, parent):
        super().__init__(parent)
        self._update_timer = None
        self._memory_update_after = None
        self._last_memory_update = 0
        self._memory_update_interval = 15000  # 15 seconds
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
            text="Models: Checking...",
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
            text="Memory: --",
            text_color="gray"
        )
        self.memory_label.pack(side="right", padx=20)
        
        # Start memory monitoring with throttling
        self._schedule_memory_update()
        
    def toggle_theme(self):
        current = ctk.get_appearance_mode().lower()
        new_theme = "light" if current == "dark" else "dark"
        ctk.set_appearance_mode(new_theme)
        self.theme_btn.configure(text=f"Theme: {new_theme.capitalize()}")
        
    def _schedule_memory_update(self):
        """Schedule the next memory update with throttling"""
        current_time = time.time() * 1000
        if current_time - self._last_memory_update >= self._memory_update_interval:
            self._update_memory()
            self._last_memory_update = current_time
            
        # Schedule next update
        if self._memory_update_after:
            self.after_cancel(self._memory_update_after)
        self._memory_update_after = self.after(self._memory_update_interval, self._schedule_memory_update)
        
    def _update_memory(self):
        """Update memory usage indicator"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.configure(text=f"Memory: {memory_mb:.1f}MB")
        except Exception as e:
            logger.error(f"Failed to update memory usage: {e}")
        
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

class InputPane(ctk.CTkFrame):
    """Enhanced input pane with template support and line numbers"""
    def __init__(self, parent):
        super().__init__(parent)
        self.after_id = None
        self.setup_ui()
        
    def setup_ui(self):
        # Template selector frame
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
        self.line_numbers.configure(state="disabled")
        
        self.text = ctk.CTkTextbox(
            self.input_frame,
            font=("Arial", 12),
            wrap="word"
        )
        self.text.pack(side="left", fill="both", expand=True)
        
        # Bind events with debouncing
        self.text.bind("<<Modified>>", self.on_text_change)
        self.text.bind("<Key>", self.schedule_line_numbers_update)
        
    def on_text_change(self, event=None):
        """Handle text changes with debouncing"""
        content = self.text.get("1.0", "end-1c")
        char_count = len(content)
        self.char_count.configure(text=f"Characters: {char_count}")
        self.text.edit_modified(False)
        
    def schedule_line_numbers_update(self, event=None):
        """Schedule line numbers update with debouncing"""
        if self.after_id:
            self.after_cancel(self.after_id)
        self.after_id = self.after(100, self.update_line_numbers)
        
    def update_line_numbers(self):
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
            "Analysis": "Please analyze this:\n\n",
            "Story": "Write a story about:\n\n",
            "Code Review": "Please review this code:\n\n",
            "Bug Report": "Bug Description:\n\nSteps to Reproduce:\n\nExpected Result:\n\nActual Result:\n"
        }
        
        if template_name != "None":
            self.text.delete("1.0", "end")
            self.text.insert("1.0", templates.get(template_name, ""))
            self.update_line_numbers()

class OutputPane(ctk.CTkFrame):
    """Enhanced output pane with search and format options"""
    def __init__(self, parent):
        super().__init__(parent)
        self.last_search_pos = "1.0"
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
            command=lambda: self.find_text()
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
        self.text.bind("<<Modified>>", self.update_counts)
        
    def format_output(self, format_type):
        """Format the output text based on selected format"""
        if not self.text.get("1.0", "end-1c").strip():
            return
            
        content = self.text.get("1.0", "end-1c")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        
        try:
            if format_type == "Code":
                content = "```\n" + content + "\n```"
            elif format_type == "JSON":
                parsed = json.loads(content)
                content = json.dumps(parsed, indent=2)
                
            self.text.insert("1.0", content)
        except Exception as e:
            logger.error(f"Format error: {e}")
            self.text.insert("1.0", content)
            
        self.text.configure(state="disabled")
        self.update_counts()
        
    def update_counts(self, event=None):
        """Update word and character counts"""
        if event:
            self.text.edit_modified(False)
            
        content = self.text.get("1.0", "end-1c")
        words = len(content.split())
        chars = len(content)
        self.count_label.configure(
            text=f"Words: {words} | Characters: {chars}"
        )
        
    def find_text(self, backwards=False):
        """Search for text in output with wraparound"""
        search_text = self.search_entry.get()
        if not search_text:
            return
            
        start_pos = self.text.index("insert")
        if backwards:
            pos = self.text.search(
                search_text,
                start_pos,
                backwards=True,
                stopindex="1.0"
            )
        else:
            pos = self.text.search(
                search_text,
                start_pos,
                stopindex="end"
            )
            
        if pos:
            line, char = map(int, pos.split('.'))
            end_pos = f"{line}.{char + len(search_text)}"
            
            self.text.tag_remove("search", "1.0", "end")
            self.text.tag_add("search", pos, end_pos)
            self.text.tag_configure("search", background="yellow")
            self.text.see(pos)
            self.text.mark_set("insert", pos)
            
        elif not backwards:
            # Start from beginning if not found
            self.text.mark_set("insert", "1.0")
            self.find_text()
        else:
            # Start from end if not found
            self.text.mark_set("insert", "end")
            self.find_text(backwards=True)

def create_status_bar(root):
    """Create and return a status bar"""
    status_bar = StatusBar(root)
    status_bar.pack(side="bottom", fill="x")
    return status_bar

def create_toolbar(root):
    """Create and return a toolbar"""
    toolbar = ctk.CTkFrame(root)
    
    buttons = [
        ("New", lambda: clear_output()),
        ("Copy", lambda: copy_to_clipboard()),
        ("Save", lambda: save_output()),
        ("Export History", lambda: export_history())
    ]
    
    for text, command in buttons:
        btn = ctk.CTkButton(
            toolbar,
            text=text,
            command=command,
            width=100
        )
        btn.pack(side="left", padx=5)
        
    return toolbar

def create_scrolled_text(root, height=10, width=50, readonly=False):
    """Create and return a scrolled text widget"""
    text = ctk.CTkTextbox(
        root,
        height=height,
        width=width,
        font=("Arial", 12),
        wrap="word",
        state="disabled" if readonly else "normal"
    )
    return text

def create_model_indicators(root, models):
    """Create indicator labels for each model"""
    frame = ctk.CTkFrame(root)
    indicators = {}
    
    for model_type in models:
        label = ctk.CTkLabel(
            frame,
            text=model_type.capitalize(),
            text_color="gray"
        )
        label.pack(side="left", padx=5)
        indicators[model_type] = label
        
    return frame, indicators

def update_output(text, is_error=False):
    """Update output text widget with new content"""
    if not hasattr(update_output, "output_widget"):
        logger.error("Output widget not set")
        return
        
    try:
        update_output.output_widget.configure(state="normal")
        update_output.output_widget.delete("1.0", "end")
        text = sanitize_output(text)
        update_output.output_widget.insert("end", text)
            
        if is_error:
            update_output.output_widget.tag_add("error", "1.0", "end")
            update_output.output_widget.tag_configure("error", foreground="red")
            
        update_output.output_widget.configure(state="disabled")
        update_output.output_widget.see("end")
        
    except Exception as e:
        logger.error(f"Failed to update output: {e}")

def sanitize_output(text):
    """Clean up the output text"""
    if not text:
        return ""
        
    # Remove common formatting artifacts
    text = text.replace("```", "").replace("**", "")
    text = text.replace("#", "").replace("`", "")
    
    # Clean meta instructions
    if "PRESENT TO USER:" in text:
        text = text.split("PRESENT TO USER:", 1)[1]
        
    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    
    return text.strip()

def clear_output():
    """Clear the output text widget"""
    if hasattr(update_output, "output_widget"):
        update_output.output_widget.configure(state="normal")
        update_output.output_widget.delete("1.0", "end")
        update_output.output_widget.configure(state="disabled")

def copy_to_clipboard():
    """Copy output text to clipboard"""
    if hasattr(update_output, "output_widget"):
        text = update_output.output_widget.get("1.0", "end").strip()
        update_output.output_widget.clipboard_clear()
        update_output.output_widget.clipboard_append(text)
        update_output.output_widget.update()

def save_output():
    """Save output text to file"""
    if hasattr(update_output, "output_widget"):
        text = update_output.output_widget.get("1.0", "end").strip()
        if text:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                except Exception as e:
                    logger.error(f"Failed to save output: {e}")
                    messagebox.showerror("Error", f"Failed to save file: {e}")

def export_history():
    """Export processing history to JSON file"""
    from main import app_state
    
    if app_state and app_state.processing_history:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(app_state.processing_history.history, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to export history: {e}")
                messagebox.showerror("Error", f"Failed to export history: {e}")

def handle_phase_error(phase_name, error, progress_tracker, loading_indicator, current_output):
    """Handle errors during processing phases"""
    error_msg = f"\nError in {phase_name} phase: {str(error)}\n"
    logger.error(f"{phase_name} phase error: {error}")
    
    if "timeout" in str(error).lower():
        error_msg += "\nThe model took too long to respond. Please try again."
    elif isinstance(error, Exception):
        error_msg += "\nPlease ensure Ollama is running and try again."
    else:
        error_msg += f"\nUnexpected error. Check the logs for details."
        
    if current_output:
        error_msg = f"{current_output}\n{error_msg}"
        
    if loading_indicator:
        loading_indicator.stop()
        
    return error_msg

class OutputHandler:
    """Handles output text updates safely"""
    @staticmethod
    def update(text_widget, text, is_error=False):
        try:
            text_widget.configure(state="normal")
            text_widget.delete("1.0", "end")
            text = sanitize_output(text)
            text_widget.insert("end", text)
            
            if is_error:
                text_widget.tag_add("error", "1.0", "end")
                text_widget.tag_configure("error", foreground="red")
                
            text_widget.configure(state="disabled")
            text_widget.see("end")
            
        except Exception as e:
            logger.error(f"Failed to update output: {e}")

def reset_ui_state():
    """Reset UI elements to initial state"""
    if hasattr(update_output, "output_widget"):
        clear_output()
    
    from main import app_state
    if app_state:
        app_state.reset_indicators()
        if app_state.status_bar:
            app_state.status_bar.set_status("Ready")
        if app_state.loading:
            app_state.loading.stop()