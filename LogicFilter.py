import tkinter as tk

import ollama

# Configuration for Ollama models
OLLAMA_MODELS = {
    "analysis": "llama3.2:latest",  # Model for initial analysis
    "generation": "olmo2:13b",  # Model for solution generation
    "vetting": "phi4:latest",  # Model for final refinement
}


def analyze_prompt(prompt, model_name):
    """
    Analyzes the initial prompt to identify core components, implicit assumptions,
    potential ambiguities, and inherent challenges.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Analyze the following prompt: '{prompt}'. "
                    "Break it down into its core components, identify "
                    "implicit assumptions, potential ambiguities, and any "
                    "inherent challenges. Provide a detailed analysis report."
                ),
            }
        ]
        response = ollama.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Error during analysis: {e}")
        return None


def generate_solutions(analysis_report, model_name):
    """
    Generates multiple potential solutions or alternative phrasings based on the analysis report.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Based on the following analysis report: '{analysis_report}', "
                    "generate multiple potential solutions, approaches, or alternative "
                    "phrasings for the original prompt. Explore different angles and "
                    "perspectives. Provide a list of candidate prompts."
                ),
            }
        ]
        response = ollama.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Error during solution generation: {e}")
        return None


def vet_and_refine(candidate_prompts, model_name):
    """
    Evaluates candidate prompts, identifies issues, and provides improvements.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Analyze and improve the following prompts: '{candidate_prompts}'\n\n"
                    "1. Identify specific issues in each prompt (ambiguity, inconsistency, incompleteness)\n"
                    "2. For each identified issue, explain the problem and provide a concrete fix\n"
                    "3. Generate an improved version that addresses all issues\n\n"
                    "Format your response as:\n"
                    "ISSUES FOUND:\n"
                    "[List each issue with explanation]\n\n"
                    "IMPROVEMENTS MADE:\n"
                    "[List specific changes made]\n\n"
                    "FINAL IMPROVED VERSION:\n"
                    "[The complete improved prompt]"
                ),
            }
        ]
        response = ollama.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Error during refinement: {e}")
        return None


def create_scrolled_text(parent, readonly=False):
    """Helper function to create a Text widget with a scrollbar."""
    frame = tk.Frame(parent)

    # Create scrollbar
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create text widget
    text_widget = tk.Text(
        frame,
        yscrollcommand=scrollbar.set,
        wrap=tk.WORD,
        font=("Arial", 10),
        undo=True,
    )

    if readonly:
        text_widget.config(state=tk.DISABLED)

    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Configure scrollbar
    scrollbar.config(command=text_widget.yview)

    return frame, text_widget


def main():
    """
    Main function to orchestrate the multi-tiered reasoning process.
    """
    progress_msgs = {
        "start": "Starting prompt analysis and improvement process...\n",
        "analyzing": "🔍 Phase 1/3: Analyzing your prompt...\n",
        "analysis_done": "✓ Analysis complete!\n\n",
        "generating": "🤔 Phase 2/3: Generating alternative solutions...\n",
        "generation_done": "✓ Solutions generated!\n\n",
        "refining": "✨ Phase 3/3: Refining and preparing final version...\n",
        "complete": "✓ Process complete! Here's your improved prompt:\n\n",
    }

    root = tk.Tk()
    root.title("Prompt Filter")
    root.configure(bg="#f0f0f0")
    root.minsize(800, 600)

    # Main container with padding
    main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Input section
    input_label = tk.Label(
        main_frame, text="Enter your prompt:", font=("Arial", 12, "bold"), bg="#f0f0f0"
    )
    input_label.pack(anchor=tk.W)

    input_frame, input_text = create_scrolled_text(main_frame)
    input_frame.pack(fill=tk.X, pady=(5, 15))

    # Output section
    output_label = tk.Label(
        main_frame, text="Results:", font=("Arial", 12, "bold"), bg="#f0f0f0"
    )
    output_label.pack(anchor=tk.W)

    output_frame, output_text = create_scrolled_text(main_frame, readonly=True)
    output_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 15))

    def update_output(text):
        """Helper function to update output text."""
        output_text.config(state=tk.NORMAL)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, text)
        output_text.config(state=tk.DISABLED)
        output_text.see(tk.END)

    def process_prompt():
        initial_prompt = input_text.get("1.0", tk.END).strip()
        if not initial_prompt:
            update_output("⚠️ Error: No prompt entered.")
            return

        output = progress_msgs["start"]
        update_output(output)

        # Phase 1: Analysis
        output += progress_msgs["analyzing"]
        update_output(output)

        analysis_report = analyze_prompt(initial_prompt, OLLAMA_MODELS["analysis"])
        if not analysis_report:
            update_output(output + "❌ Error: Analysis failed.")
            return

        output += progress_msgs["analysis_done"]
        output += "📋 Analysis Results:\n"
        output += "=" * 40 + "\n"
        output += analysis_report + "\n\n"
        update_output(output)

        # Phase 2: Solution Generation
        output += progress_msgs["generating"]
        update_output(output)

        solutions = generate_solutions(analysis_report, OLLAMA_MODELS["generation"])
        if not solutions:
            update_output(output + "❌ Error: Solution generation failed.")
            return

        output += progress_msgs["generation_done"]
        output += "💡 Generated Solutions:\n"
        output += "=" * 40 + "\n"
        output += solutions + "\n\n"
        update_output(output)

        # Phase 3: Final Refinement
        output += progress_msgs["refining"]
        update_output(output)

        improvements = vet_and_refine(solutions, OLLAMA_MODELS["vetting"])
        if not improvements:
            update_output(output + "❌ Error: Refinement failed.")
            return

        output += progress_msgs["complete"]
        output += "🎯 Final Result:\n"
        output += "=" * 40 + "\n"
        output += improvements
        update_output(output)

    # Process button with improved styling
    process_button = tk.Button(
        main_frame,
        text="Process & Improve Prompt",
        command=process_prompt,
        font=("Arial", 11),
        bg="#4a90e2",
        fg="white",
        padx=20,
        pady=10,
        relief=tk.RAISED,
        cursor="hand2",
    )
    process_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
