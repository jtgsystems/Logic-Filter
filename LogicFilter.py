import tkinter as tk

import ollama

# import json  # Unused import
# import os  # Unused import

# Configuration (can be loaded from a file or command-line arguments)
OLLAMA_MODELS = {
    "analysis": "llama3.2:latest",  # Replace with your desired model
    "generation": "llama2:13b",  # Replace with your desired model
    "vetting": "phi4:latest",  # Replace with your desired model
}


def analyze_prompt(prompt, model_name):
    """
    Analyzes the initial prompt, breaking it down into its core components,
    identifying implicit assumptions, potential ambiguities, and any inherent challenges.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Analyze the following prompt: '{prompt}'. "
                    "Break it down into its core components, identify "
                    "implicit assumptions, potential ambiguities, and any "
                    "inherent challenges. Provide a detailed analysis "
                    "report."
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
    Generates multiple potential solutions, approaches, or alternative phrasings for the prompt.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Based on the following analysis report: '{analysis_report}', "
                    "generate multiple potential solutions, approaches, or "
                    "alternative phrasings for the original prompt. Explore "
                    "different angles and perspectives. Provide a list of "
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
    Evaluates each candidate prompt based on criteria such as clarity, coherence,
    completeness, and potential effectiveness. Identifies weaknesses, inconsistencies,
    or areas for improvement. Refines the best candidate prompt based on the evaluation.
    """
    try:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Evaluate the following candidate prompts: '{candidate_prompts}'. "
                    "Based on criteria such as clarity, coherence, completeness, and "
                    "potential effectiveness, identify weaknesses, inconsistencies, or "
                    "areas for improvement. Refine the best candidate prompt based on "
                    "the evaluation. Provide the final, vetted prompt."
                ),
            }
        ]
        response = ollama.chat(model=model_name, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Error during vetting and refinement: {e}")
        return None


def main():
    """
    Main function to orchestrate the multi-tiered reasoning process.
    """
    root = tk.Tk()  # Used for GUI elements
    root.title("Prompt Filter")

    text_box = tk.Text(root, height=10, width=50)
    text_box.pack(pady=10)

    def process_prompt():
        initial_prompt = text_box.get("1.0", tk.END).strip()
        if not initial_prompt:
            print("No prompt entered.")
            return

        # Layer 1: Analysis
        analysis_report = analyze_prompt(initial_prompt, OLLAMA_MODELS["analysis"])
        if not analysis_report:
            print("Analysis failed. Exiting.")
            return
        print("\nAnalysis Report:\n", analysis_report)

        # Layer 2: Solution Generation
        candidate_prompts_str = generate_solutions(
            analysis_report, OLLAMA_MODELS["generation"]
        )
        if not candidate_prompts_str:
            print("Solution generation failed. Exiting.")
            return
        print("\nCandidate Prompts:\n", candidate_prompts_str)

        # Layer 3: Vetting and Refinement
        final_prompt = vet_and_refine(candidate_prompts_str, OLLAMA_MODELS["vetting"])
        if not final_prompt:
            print("Vetting and refinement failed. Exiting.")
            return
        print("\nFinal Vetted Prompt:\n", final_prompt)

    process_button = tk.Button(root, text="Process Prompt", command=process_prompt)
    process_button.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
