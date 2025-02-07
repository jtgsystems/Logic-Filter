import tkinter as tk
import ollama

# Configuration
OLLAMA_MODELS = {
    "analysis": "llama3.2:latest",
    "generation": "olmo2:13b",
    "vetting": "deepseek-r1",
    "finalization": "deepseek-r1:14b",  # Use deepseek-r1:14b for finalization
}

# Progress messages
PROGRESS_MESSAGES = {
    "start": "Starting prompt analysis and improvement process...\n",
    "analyzing": "🔍 Phase 1/4: Analyzing your prompt...\n",
    "analysis_done": "✓ Analysis complete!\n\n",
    "generating": "🤔 Phase 2/4: Generating alternative solutions...\n",
    "generation_done": "✓ Solutions generated!\n\n",
    "vetting": "🔎 Phase 3/4: Vetting and screening solutions...\n",
    "vetting_done": "✓ Vetting complete!\n\n",
    "finalizing": "📝 Phase 4/4: Preparing final prompt...\n",
    "complete": "✓ Process complete!\n\n"
}


def analyze_prompt(prompt, model_name):
    """
    Analyzes the initial prompt.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Analyze the following prompt: '{prompt}'. "
                    "Break it down, identify assumptions, ambiguities, and "
                    "challenges. Provide a detailed analysis report."
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
    Generates multiple potential solutions/alternative phrasings.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Based on this analysis: '{analysis_report}', "
                    "generate multiple solutions or alternative phrasings. "
                    "Explore different perspectives. Provide a list of "
                    "candidate prompts."
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
    Vets, screens, and identifies expansion opportunities in candidate prompts.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Analyze the following candidate prompts: '{candidate_prompts}'\n\n"
                    "1. Evaluate clarity, coherence, completeness, and potential for expansion.\n"
                    "2. Identify weaknesses, inconsistencies, and missing elements.\n"
                    "3. Suggest specific areas where the prompt could be expanded or enhanced.\n"
                    "4. Provide a detailed report. Do NOT provide a final prompt, only the analysis."
                ),
            }
        ]
        response = ollama.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Error during vetting: {e}")
        return None


def finalize_prompt(vetting_report, original_prompt, model_name):
    """
    Creates the final, expanded "super prompt" based on the vetting report and original.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Original Prompt: {original_prompt}\n\n"
                    f"Vetting Report (including expansion opportunities): {vetting_report}\n\n"
                    "Create the final, improved prompt using the following guidelines:\n"
                    "1. Start with clear, precise instructions.\n"
                    "2. Include specific details about context, outcome, length, format, and style.\n"
                    "3. Provide examples of the desired output format, if possible.\n"
                    "4. Use appropriate leading words or phrases.\n"
                    "5. Avoid vague or imprecise language.\n"
                    "6. Provide guidance on what *should* be done, not just what *shouldn't*.\n\n"
                    "Address all issues and incorporate all expansion opportunities "
                    "identified in the vetting report. Expand the prompt to include any "
                    "missing elements, making it a 'super prompt' that is comprehensive, "
                    "detailed, and requires no further modification. Be extremely thorough. "
                    "The response should be a complete, production-ready prompt."
                )
            }
        ]
        response = ollama.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Error during finalization: {e}")
        return None


def create_scrolled_text(parent, height=10, width=50, readonly=False):
    """Helper function to create a Text widget with a scrollbar."""
    frame = tk.Frame(parent)

    # Create scrollbar
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create text widget
    text_widget = tk.Text(
        frame,
        height=height,
        width=width,
        yscrollcommand=scrollbar.set,
        wrap=tk.WORD,
        font=("Arial", 10)
    )

    if readonly:
        text_widget.config(state=tk.DISABLED)

    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Configure scrollbar
    scrollbar.config(command=text_widget.yview)

    return frame, text_widget


def main():
    """
    Main function.
    """
    # Progress messages
    progress_msgs = {
        "start": "Starting prompt analysis and improvement process...\n",
        "analyzing": "🔍 Phase 1/4: Analyzing your prompt...\n",
        "analysis_done": "✓ Analysis complete!\n\n",
        "generating": "🤔 Phase 2/4: Generating alternative solutions...\n",
        "generation_done": "✓ Solutions generated!\n\n",
        "vetting": "🔎 Phase 3/4: Vetting and screening solutions...\n",
        "vetting_done": "✓ Vetting complete!\n\n",
        "finalizing": "📝 Phase 4/4: Preparing final prompt...\n",
        "complete": "✓ Process complete!\n\n"
    }

    root = tk.Tk()
    root.title("Prompt Filter")
    root.configure(bg="#f0f0f0")

    # Set minimum window size
    root.minsize(800, 600)

    # Main container with padding
    main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Input section
    input_label = tk.Label(
        main_frame,
        text="Enter your prompt:",
        font=("Arial", 12, "bold"),
        bg="#f0f0f0"
    )
    input_label.pack(anchor=tk.W)

    input_frame, input_text = create_scrolled_text(
        main_frame,
        height=5,
        width=60
    )
    input_frame.pack(fill=tk.X, pady=(5, 15))

    # Output section
    output_label = tk.Label(
        main_frame,
        text="Results:",
        font=("Arial", 12, "bold"),
        bg="#f0f0f0"
    )
    output_label.pack(anchor=tk.W)

    output_frame, output_text = create_scrolled_text(
        main_frame,
        height=20,
        width=60,
        readonly=True
    )
    output_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 15))

    def update_output(text):
        """Updates the output text area."""
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

        # --- Phase 1: Analysis ---
        output += progress_msgs["analyzing"]
        update_output(output)

        analysis_report = analyze_prompt(
            initial_prompt,
            OLLAMA_MODELS["analysis"]
        )
        if not analysis_report:
            update_output(output + "❌ Error: Analysis failed.")
            return

        output += progress_msgs["analysis_done"]
        output += "🔍 Prompt Analysis:\n"
        output += "─" * 40 + "\n"
        output += analysis_report + "\n\n"
        update_output(output)

        # --- Phase 2: Solution Generation ---
        output += progress_msgs["generating"]
        update_output(output)

        # DEBUG: Check input to generate_solutions
        update_output(f"DEBUG: Input to generate_solutions: {analysis_report}\n")

        solutions = generate_solutions(
            analysis_report,
            OLLAMA_MODELS["generation"]
        )
        if not solutions:
            update_output(output + "❌ Error: Solution generation failed.")
            return

        output += progress_msgs["generation_done"]
        output += "💡 Generated Solutions:\n"
        output += "─" * 40 + "\n"
        output += solutions + "\n\n"
        update_output(output)

        # --- Phase 3: Vetting ---
        output += progress_msgs["vetting"]
        update_output(output)

        # DEBUG: Check input to vet_and_refine
        update_output(f"DEBUG: Input to vet_and_refine: {solutions}\n")

        vetting_report = vet_and_refine(
            solutions,
            OLLAMA_MODELS["vetting"]
        )
        if not vetting_report:
            update_output(output + "❌ Error: Vetting failed.")
            return

        output += progress_msgs["vetting_done"]
        output += "🔎 Vetting Report:\n"
        output += "─" * 40 + "\n"
        output += vetting_report + "\n\n"
        update_output(output)

        # --- Phase 4: Final Prompt ---
        output += progress_msgs["finalizing"]
        update_output(output)

        # DEBUG: Check input to finalize_prompt
        update_output(f"DEBUG: Input to finalize_prompt: {vetting_report}, {initial_prompt}\n")

        final_result = finalize_prompt(
            vetting_report,
            initial_prompt,
            OLLAMA_MODELS["finalization"]
        )
        if not final_result:
            update_output(output + "❌ Error: Final prompt creation failed.")
            return

        output += progress_msgs["complete"]
        output += "✅ Final Improved Prompt:\n"
        output += "═" * 40 + "\n"
        output += final_result + "\n"
        update_output(output)

    # Process button
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
        cursor="hand2"
    )
    process_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
