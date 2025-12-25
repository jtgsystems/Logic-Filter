import ollama
import logging
from typing import Dict, List
import re

# Set up logging
logging.basicConfig(filename='problem_solver.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Cache for solutions
solution_cache: Dict[str, str] = {}

def get_solution(full_prompt: str, model: str = 'phi4:latest', debug: bool = False) -> str:
    """Retrieve a solution from the Ollama model using a custom prompt."""
    try:
        response = ollama.generate(model=model, prompt=full_prompt)
        solution = response['response'].strip()
        
        if debug:
            print(f"\n[DEBUG] Prompt: {full_prompt}")
            print(f"[DEBUG] Raw Response: {solution}")
        
        # Check if the solution is too short or contains "what" (indicating nonsense)
        if len(solution) < 50 or "what" in solution.lower() or "sorry" in solution.lower():
            logging.warning(f"Model {model} gave a weak response: {solution}")
            return ""
        
        return solution
    except Exception as e:
        logging.error(f"Error with model {model}: {e}")
        return ""

def decompose_problem(problem: str, debug: bool = False) -> List[str]:
    """Break the problem into sub-problems."""
    try:
        prompt = f"Break this problem into smaller, manageable sub-problems: {problem}"
        response = ollama.generate(model='phi4:latest', prompt=prompt)
        lines = response['response'].split('\n')
        sub_problems = []
        for line in lines:
            line = line.strip()
            if line:
                # Check for numbered lists (e.g., "1. ", "2. ")
                if re.match(r"^\\d+\\.\\s", line):
                    sub_problems.append(line.split('.', 1)[1].strip())
                # Check for bullet points (e.g., "- ", "* ")
                elif line.startswith(('-', '*')):
                    sub_problems.append(line[1:].strip())
                else:
                    sub_problems.append(line)
        if debug:
            print(f"\n[DEBUG] Decomposition Prompt: {prompt}")
            print(f"[DEBUG] Sub-problems: {sub_problems}")
        if not sub_problems:
            return [problem]
        logging.info(f"Decomposed problem into: {sub_problems}")
        return sub_problems
    except Exception as e:
        logging.error(f"Error decomposing problem: {e}")
        return [problem]

def validate_solution(solution: str, problem: str) -> bool:
    """Ask the user to validate the solution."""
    print(f"\nProposed Solution for '{problem}':\n{solution}")
    while True:
        correct = input("Is this solution correct? (yes/no): ").lower().strip()
        if correct == 'yes':
            print("Solution confirmed as correct. Proceeding...")
            return True
        elif correct == 'no':
            return False
        print("Please enter 'yes' or 'no'.")

def get_user_feedback() -> str:
    """Collect specific feedback to refine the solution."""
    return input("What needs to be changed or added to make this solution correct? ").strip()

def combine_solutions(solutions: List[str]) -> str:
    """Combine sub-solutions into a cohesive whole."""
    if len(solutions) == 1:
        return solutions[0]
    return "\n".join([f"Step {i+1}: {sol}" for i, sol in enumerate(solutions)])

def solve_problem(problem: str, max_retries: int = 3, debug: bool = False) -> str:
    """Solve the problem with an optimized flow."""
    logging.info(f"Attempting to solve: {problem}")
    print(f"\nAttempting to solve: {problem}")
    
    model = 'phi4:latest'
    if problem.startswith("decompose"):
        model = 'qwq:latest'
    elif problem.startswith("solve"):
        model = 'deepseek-r1:32b'
    
    if problem in solution_cache:
        logging.info(f"Retrieved from cache: {problem}")
        print("Solution retrieved from cache.")
        return solution_cache[problem]

    # Step 1: Try solving the problem directly
    print("Attempting a direct solution...")
    direct_prompt = (f"Provide a detailed, step-by-step solution to this problem: {problem}. "
                     f"Do not ask for clarification or repeat the problem—solve it directly.")
    direct_solution = get_solution(direct_prompt, model=model, debug=debug)
    if direct_solution and validate_solution(direct_solution, problem):
        solution_cache[problem] = direct_solution
        logging.info(f"Solved and cached directly: {problem}")
        return direct_solution

    # Step 2: If direct solution fails, decompose and solve sub-problems
    print("Direct solution not accepted. Decomposing into sub-problems...")
    sub_problems = decompose_problem(problem, debug)
    solutions = []

    for idx, sub_problem in enumerate(sub_problems, 1):
        print(f"\nSolving sub-problem {idx} of {len(sub_problems)}: {sub_problem}")
        attempts = 0
        current_prompt = (f"Provide a detailed, step-by-step solution to this sub-problem: {sub_problem}. "
                          f"Do not ask for clarification or repeat the problem—solve it directly.")

        while attempts < max_retries:
            solution = get_solution(current_prompt, model=model, debug=debug)
            if not solution:
                attempts += 1
                logging.info(f"Retry {attempts} for '{sub_problem}'")
                print(f"Retrying ({attempts}/{max_retries})...")
                continue

            if validate_solution(solution, sub_problem):
                solutions.append(solution)
                break
            else:
                feedback = get_user_feedback()
                if not feedback:
                    feedback = "Please try a different approach."
                current_prompt = (f"Provide a detailed, step-by-step solution to this sub-problem: {sub_problem}, "
                                  f"ensuring that {feedback}. Do not ask for clarification or repeat the problem—solve it directly.")
                attempts += 1

            if attempts >= max_retries:
                return f"Sorry, I couldn't solve '{sub_problem}' after {max_retries} attempts."

    # Step 3: Combine and validate the final solution
    combined_solution = combine_solutions(solutions)
    print("\nCombined Solution:")
    if validate_solution(combined_solution, problem):
        solution_cache[problem] = combined_solution
        logging.info(f"Solved and cached: {problem}")
        return combined_solution
    return "Sorry, the combined solution didn’t meet your expectations."

def main():
    """Main interaction loop."""
    print("Welcome to the Enhanced Problem Solver!")
    print("Type your problem, and I’ll solve it step-by-step.\n")

    debug_mode = input("Enable debug mode to see prompts/responses? (yes/no): ").lower() == 'yes'

    while True:
        problem = input("Enter your problem (or 'quit' to exit): ").strip()
        if not problem:
            print("Please enter a problem.")
            continue
        if problem.lower() == 'quit':
            break

        solution = solve_problem(problem, debug=debug_mode)
        print("\nFinal Solution:")
        print(solution)

        while True:
            another = input("\nSolve another problem? (yes/no): ").lower().strip()
            if another in ['yes', 'no']:
                break
            print("Please enter 'yes' or 'no'.")
        if another != 'yes':
            break

    print("\nThanks for using the Enhanced Problem Solver!")

if __name__ == "__main__":
    main()