import tkinter as tk

import ollama

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
        print(f"Error during analysis: {e}")
        return None


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
                ),
            }
        ]
        response = ollama.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Error during solution generation: {e}")
        return None


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
        print(f"Error during vetting: {e}")
        return None


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
        print(f"Error during finalization: {e}")
        return None


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
        print(f"Error during enhancement: {e}")
        return None


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
        response = ollama.chat(model=model_name, messages=messages)
        improved = response["message"]["content"]

        # Then use deepseek-r1:14b as final presenter
        messages = [
            {
                "role": "user",
                "content": (
                    "You are the final presenter. Review this prompt and "
                    "ensure it's presented in the cleanest possible "
                    f"format:\n\n{improved}\n\n"
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
        print(f"Error during comprehensive review: {e}")
        return None


def create_model_indicators(parent):
    """Creates a frame with model status indicators."""
    frame = tk.Frame(parent, bg="#f0f0f0")
    frame.pack(fill=tk.X, pady=(0, 10))

    indicators = {}
    for model_type in OLLAMA_MODELS:
        label = tk.Label(
            frame,
            text=f"● {model_type}",
            font=("Arial", 9),
            fg="#666666",
            bg="#f0f0f0",
            padx=5,
        )
        label.pack(side=tk.LEFT)
        indicators[model_type] = label

    return indicators


def create_scrolled_text(parent, height=10, width=50, readonly=False):
    """Helper function to create a Text widget with a scrollbar."""
    frame = tk.Frame(parent)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_widget = tk.Text(
        frame,
        height=height,
        width=width,
        yscrollcommand=scrollbar.set,
        wrap=tk.WORD,
        font=("Arial", 10),
    )

    if readonly:
        text_widget.config(state=tk.DISABLED)

    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=text_widget.yview)

    return frame, text_widget


def main():
    """Main function."""
    progress_msgs = PROGRESS_MESSAGES

    root = tk.Tk()
    root.title("Prompt Filter")
    root.configure(bg="#f0f0f0")
    root.minsize(800, 600)

    main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Create model status indicators
    model_indicators = create_model_indicators(main_frame)

    # Reset all indicators to inactive
    def reset_indicators():
        for label in model_indicators.values():
            label.config(fg="#666666")

    # Set an indicator as active
    def set_active_model(model_type):
        reset_indicators()
        model_indicators[model_type].config(fg="#4a90e2")

    input_label = tk.Label(
        main_frame,
        text="Enter your prompt:",
        font=("Arial", 12, "bold"),
        bg="#f0f0f0",
    )
    input_label.pack(anchor=tk.W)

    input_frame, input_text = create_scrolled_text(
        main_frame,
        height=5,
        width=60,
    )
    input_frame.pack(fill=tk.X, pady=(5, 15))

    output_label = tk.Label(
        main_frame,
        text="Results:",
        font=("Arial", 12, "bold"),
        bg="#f0f0f0",
    )
    output_label.pack(anchor=tk.W)

    output_frame, output_text = create_scrolled_text(
        main_frame,
        height=20,
        width=60,
        readonly=True,
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
            update_output("Error: No prompt entered.")
            return

        output = progress_msgs["start"]
        update_output(output)

        # Phase 1: Analysis
        set_active_model("analysis")
        output += progress_msgs["analyzing"]
        update_output(output)

        analysis_report = analyze_prompt(
            initial_prompt,
            OLLAMA_MODELS["analysis"],
        )
        if not analysis_report:
            update_output(output + "Error: Analysis failed.")
            return

        output += progress_msgs["analysis_done"]
        output += analysis_report + "\n\n"
        update_output(output)

        # Phase 2: Solution Generation
        set_active_model("generation")
        output += progress_msgs["generating"]
        update_output(output)

        solutions = generate_solutions(
            analysis_report,
            OLLAMA_MODELS["generation"],
        )
        if not solutions:
            update_output(output + "Error: Generation failed.")
            return

        output += progress_msgs["generation_done"]
        output += solutions + "\n\n"
        update_output(output)

        # Phase 3: Vetting
        set_active_model("vetting")
        output += progress_msgs["vetting"]
        update_output(output)

        vetting_report = vet_and_refine(
            solutions,
            OLLAMA_MODELS["vetting"],
        )
        if not vetting_report:
            update_output(output + "Error: Vetting failed.")
            return

        output += progress_msgs["vetting_done"]
        output += vetting_report + "\n\n"
        update_output(output)

        # Phase 4: Initial Finalization
        set_active_model("finalization")
        output += progress_msgs["finalizing"]
        update_output(output)

        final_result = finalize_prompt(
            vetting_report,
            initial_prompt,
            OLLAMA_MODELS["finalization"],
        )
        if not final_result:
            update_output(output + "Error: Finalization failed.")
            return

        output += progress_msgs["finalize_done"]
        output += final_result + "\n\n"
        update_output(output)

        # Phase 5: Enhancement
        set_active_model("enhancement")
        output += progress_msgs["enhancing"]
        update_output(output)

        enhanced_result = enhance_prompt(
            final_result,
            OLLAMA_MODELS["enhancement"],
        )
        if not enhanced_result:
            update_output(output + "Error: Enhancement failed.")
            return

        output += progress_msgs["enhance_done"]
        output += enhanced_result + "\n\n"
        update_output(output)

        # Phase 6: Comprehensive Review
        set_active_model("comprehensive")
        output += progress_msgs["comprehensive"]
        update_output(output)

        comprehensive_result = comprehensive_review(
            initial_prompt,
            analysis_report,
            solutions,
            vetting_report,
            final_result,
            enhanced_result,
            OLLAMA_MODELS["comprehensive"],
        )
        if not comprehensive_result:
            update_output(output + "Error: Review failed.")
            return

        # Final presentation cleanup
        set_active_model("presenter")
        output += "Cleaning up final presentation...\n"
        update_output(output)

        # Present final result
        output += progress_msgs["complete"]
        if "PRESENT TO USER:" in comprehensive_result:
            final_text = comprehensive_result.split(
                "PRESENT TO USER:",
                1,
            )[1].strip()
            output += final_text + "\n"
        else:
            output += comprehensive_result + "\n"
        update_output(output)

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
