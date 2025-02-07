import tkinter as tk

import ollama

# Configuration
OLLAMA_MODELS = {
    "analysis": "llama3.2:latest",  # Initial deep analysis
    "generation": "olmo2:13b",  # Creative solution generation
    "vetting": "deepseek-r1",  # Initial vetting
    "finalization": "deepseek-r1:14b",  # First round improvement
    "enhancement": "phi4:latest",  # Advanced enhancement
    "comprehensive": "phi4:latest",  # Final comprehensive review (128k context)
}

# Progress messages
PROGRESS_MESSAGES = {
    "start": (
        "Starting multi-model prompt improvement process...\n"
        "This process uses multiple specialized models in sequence:\n"
        "- llama3.2:latest for deep analysis\n"
        "- olmo2:13b for creative solutions\n"
        "- deepseek-r1 for vetting\n"
        "- deepseek-r1:14b for initial improvements\n"
        "- phi4:latest for enhancement\n"
        "- phi4:latest (128k context) for final review\n\n"
    ),
    "analyzing": (
        "🔍 Phase 1/6: Initial Analysis (llama3.2:latest)\n"
        "Analyzing prompt structure, requirements, and potential...\n"
    ),
    "analysis_done": ("✓ Analysis complete! Handing off to solution generation...\n\n"),
    "generating": (
        "🤔 Phase 2/6: Solution Generation (olmo2:13b)\n"
        "Creating improvements based on analysis...\n"
    ),
    "generation_done": ("✓ Solutions generated! Handing off to vetting phase...\n\n"),
    "vetting": (
        "🔎 Phase 3/6: Solution Vetting (deepseek-r1)\n"
        "Evaluating and validating proposed improvements...\n"
    ),
    "vetting_done": ("✓ Vetting complete! Handing off to finalization...\n\n"),
    "finalizing": (
        "📝 Phase 4/6: Initial Finalization (deepseek-r1:14b)\n"
        "Creating improved version with validated changes...\n"
    ),
    "finalize_done": ("✓ Initial version complete! Handing off to enhancement...\n\n"),
    "enhancing": (
        "✨ Phase 5/6: Advanced Enhancement (phi4:latest)\n"
        "Polishing and refining the improved prompt...\n"
    ),
    "enhance_done": ("✓ Enhancement complete! Starting final review...\n\n"),
    "comprehensive": (
        "🔄 Phase 6/6: Comprehensive Review (phi4:latest)\n"
        "Using 128k context window to review entire process...\n"
    ),
    "complete": (
        "✓ Process complete!\n" "Final version combines insights from all phases.\n\n"
    ),
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


def generate_solutions(analysis_report, model_name):
    """Generates focused improvements based on the analysis."""
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Based on this analysis: '{analysis_report}'\n\n"
                    "Generate specific improvements that address the identified "
                    "needs and requirements. Focus on:\n"
                    "1. Adding missing components\n"
                    "2. Clarifying unclear parts\n"
                    "3. Strengthening weak areas\n"
                    "4. Enhancing structure and flow\n\n"
                    "Important: Stay focused on improving the original prompt. "
                    "Do not create new, unrelated prompts or go off-topic."
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
                    f"Review these suggested improvements: '{improvements}'\n\n"
                    "Evaluate how well they enhance the original prompt:\n"
                    "1. Do they address core requirements?\n"
                    "2. Are they clear and specific?\n"
                    "3. Do they maintain focus on the task?\n"
                    "4. Are they practical and implementable?\n\n"
                    "Important: Focus on validating improvements that directly "
                    "enhance the original prompt. Flag any suggestions that go "
                    "off-topic or deviate from the main goal."
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
                    "2. Adding any missing details\n"
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
    """Uses phi4's 128k context window to create the ultimate version."""
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    "Review the prompt improvement process and create the "
                    "final version:\n\n"
                    f"Original: {original_prompt}\n"
                    f"Analysis: {analysis_report}\n"
                    f"Solutions: {solutions}\n"
                    f"Vetting: {vetting_report}\n"
                    f"Final: {final_prompt}\n"
                    f"Enhanced: {enhanced_prompt}\n\n"
                    "Create the ultimate version by:\n"
                    "1. Taking the best elements from each version\n"
                    "2. Ensuring perfect clarity and structure\n"
                    "3. Maintaining complete focus on the task\n"
                    "4. Adding any final polish needed\n\n"
                    "Important: Return ONLY the final version. Stay focused "
                    "on the original task. No examples or tangents."
                ),
            }
        ]
        response = ollama.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Error during comprehensive review: {e}")
        return None


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

    input_label = tk.Label(
        main_frame, text="Enter your prompt:", font=("Arial", 12, "bold"), bg="#f0f0f0"
    )
    input_label.pack(anchor=tk.W)

    input_frame, input_text = create_scrolled_text(main_frame, height=5, width=60)
    input_frame.pack(fill=tk.X, pady=(5, 15))

    output_label = tk.Label(
        main_frame, text="Results:", font=("Arial", 12, "bold"), bg="#f0f0f0"
    )
    output_label.pack(anchor=tk.W)

    output_frame, output_text = create_scrolled_text(
        main_frame, height=20, width=60, readonly=True
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

        # Phase 1: Analysis
        output += progress_msgs["analyzing"]
        update_output(output)

        analysis_report = analyze_prompt(initial_prompt, OLLAMA_MODELS["analysis"])
        if not analysis_report:
            update_output(output + "❌ Error: Analysis failed.")
            return

        output += progress_msgs["analysis_done"]
        output += "🔍 Analysis Report:\n"
        output += "─" * 40 + "\n"
        output += analysis_report + "\n\n"
        update_output(output)

        # Phase 2: Solution Generation
        output += progress_msgs["generating"]
        update_output(output)

        solutions = generate_solutions(analysis_report, OLLAMA_MODELS["generation"])
        if not solutions:
            update_output(output + "❌ Error: Generation failed.")
            return

        output += progress_msgs["generation_done"]
        output += "💡 Solutions:\n"
        output += "─" * 40 + "\n"
        output += solutions + "\n\n"
        update_output(output)

        # Phase 3: Vetting
        output += progress_msgs["vetting"]
        update_output(output)

        vetting_report = vet_and_refine(solutions, OLLAMA_MODELS["vetting"])
        if not vetting_report:
            update_output(output + "❌ Error: Vetting failed.")
            return

        output += progress_msgs["vetting_done"]
        output += "🔎 Vetting Report:\n"
        output += "─" * 40 + "\n"
        output += vetting_report + "\n\n"
        update_output(output)

        # Phase 4: Initial Finalization
        output += progress_msgs["finalizing"]
        update_output(output)

        final_result = finalize_prompt(
            vetting_report, initial_prompt, OLLAMA_MODELS["finalization"]
        )
        if not final_result:
            update_output(output + "❌ Error: Finalization failed.")
            return

        output += progress_msgs["finalize_done"]
        output += "📝 Initial Prompt:\n"
        output += "─" * 40 + "\n"
        output += final_result + "\n\n"
        update_output(output)

        # Phase 5: Enhancement
        output += progress_msgs["enhancing"]
        update_output(output)

        enhanced_result = enhance_prompt(final_result, OLLAMA_MODELS["enhancement"])
        if not enhanced_result:
            update_output(output + "❌ Error: Enhancement failed.")
            return

        output += progress_msgs["enhance_done"]
        output += "✨ Enhanced Prompt:\n"
        output += "─" * 40 + "\n"
        output += enhanced_result + "\n\n"
        update_output(output)

        # Phase 6: Comprehensive Review
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
            update_output(output + "❌ Error: Comprehensive review failed.")
            return

        output += progress_msgs["complete"]
        output += "🌟 Ultimate Super Prompt:\n"
        output += "═" * 40 + "\n"
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
