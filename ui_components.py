import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import time
import psutil
import logging
from typing import Optional, Union, Tuple

logger = logging.getLogger("prompt_enhancer")

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

class LoadingIndicator:
    """Animated loading indicator"""
    def __init__(self, parent):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent)
        self._progress_value = 0
        self._animation_after = None
        self._animation_speed = 50
        
        self.progress = ctk.CTkProgressBar(self.frame)
        self.progress.set(0)
        self.progress.pack(pady=10, padx=20, fill="x")
        
        self.label = ctk.CTkLabel(self.frame, text="Processing...")
        self.label.pack(pady=5)
        
        self.frame.pack_forget()
        
    def start(self, progress=0):
        self._progress_value = progress / 100
        self.progress.set(self._progress_value)
        self.frame.pack(fill="x", pady=10)
        self._start_animation()
        
    def _start_animation(self):
        if self._animation_after:
            self.parent.after_cancel(self._animation_after)
            
        def animate():
            if not self.frame.winfo_ismapped():
                return
            current = self.progress.get()
            target = min(self._progress_value + 0.1, 1.0)
            if current < target:
                self.progress.set(current + 0.01)
                self._animation_after = self.parent.after(self._animation_speed, animate)
            else:
                self.progress.set(self._progress_value)
                
        self._animation_after = self.parent.after(0, animate)
        
    def stop(self):
        if self._animation_after:
            self.parent.after_cancel(self._animation_after)
            self._animation_after = None
        self.frame.pack_forget()
        
    def update_label(self, text):
        self.label.configure(text=text)

def create_status_bar(root):
    """Create and return a status bar"""
    status_bar = StatusBar(root)
    status_bar.pack(side="bottom", fill="x")
    return status_bar

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

def create_toolbar(root, input_text=None, output_text=None):
    """Create and return a toolbar"""
    toolbar = ctk.CTkFrame(root)
    
    # Create buttons with standard actions
    buttons = [
        ("New", lambda: clear_output(output_text)),
        ("Copy", lambda: copy_to_clipboard(output_text)),
        ("Save", lambda: save_output(output_text)),
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

def create_menu(root):
    """Create and return the application menu"""
    menu = tk.Menu(root)
    root.config(menu=menu)
    
    file_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="New", command=lambda: clear_output())
    file_menu.add_command(label="Save", command=lambda: save_output())
    file_menu.add_command(label="Export History", command=lambda: export_history())
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    
    edit_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Edit", menu=edit_menu)
    edit_menu.add_command(label="Copy", command=lambda: copy_to_clipboard())
    edit_menu.add_command(label="Clear Output", command=lambda: clear_output())
    
    return menu

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

def clear_output(output_text=None):
    """Clear the output text widget"""
    if output_text:
        output_text.configure(state="normal")
        output_text.delete("1.0", "end")
        output_text.configure(state="disabled")
    elif hasattr(update_output, "output_widget"):
        update_output.output_widget.configure(state="normal")
        update_output.output_widget.delete("1.0", "end")
        update_output.output_widget.configure(state="disabled")

def copy_to_clipboard(output_text=None):
    """Copy output text to clipboard"""
    if output_text:
        text = output_text.get("1.0", "end").strip()
        output_text.clipboard_clear()
        output_text.clipboard_append(text)
        output_text.update()
    elif hasattr(update_output, "output_widget"):
        text = update_output.output_widget.get("1.0", "end").strip()
        update_output.output_widget.clipboard_clear()
        update_output.output_widget.clipboard_append(text)
        update_output.output_widget.update()

def save_output(output_text=None):
    """Save output text to file"""
    text = ""
    if output_text:
        text = output_text.get("1.0", "end").strip()
    elif hasattr(update_output, "output_widget"):
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