import logging
from typing import Optional, Dict, List
from ollama_service_manager import OllamaError

logger = logging.getLogger("prompt_enhancer")

def retry_with_fallback(func, *args, max_retries=3, **kwargs):
    """Retry a function with fallback models if the primary model fails"""
    last_error = None
    model_arg_index = -1  # Find the model argument
    
    # Find which argument is the model name
    for i, arg in enumerate(args):
        if isinstance(arg, str) and arg in OLLAMA_MODELS.values():
            model_arg_index = i
            break
    
    if model_arg_index == -1:
        raise ValueError("No model argument found")
        
    current_model = args[model_arg_index]
    args = list(args)  # Convert to list for modification
    
    # Try primary model first
    for _ in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(f"Error with model {current_model}: {e}")
    
    # Try fallback models
    if current_model in FALLBACK_ORDER:
        for fallback_model in FALLBACK_ORDER[current_model]:
            args[model_arg_index] = fallback_model
            try:
                logger.info(f"Trying fallback model: {fallback_model}")
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Error with fallback model {fallback_model}: {e}")
    
    raise last_error or Exception("All models failed")

def analyze_prompt(prompt: str, model_name: str) -> str:
    """Analyze the initial prompt."""
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
                "improving this exact prompt."
            )
        }
    ]
    try:
        from main import app_state
        response = app_state.ollama_manager.chat(
            model=model_name,
            messages=messages
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise OllamaError(f"Analysis failed: {str(e)}")

def generate_solutions(analysis: str, model_name: str) -> str:
    """Generate potential improvements based on analysis."""
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
                "that directly enhance the prompt."
            )
        }
    ]
    try:
        from main import app_state
        response = app_state.ollama_manager.chat(
            model=model_name,
            messages=messages
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during solution generation: {e}")
        raise OllamaError(f"Solution generation failed: {str(e)}")

def vet_and_refine(improvements: str, model_name: str) -> str:
    """Review and validate the suggested improvements."""
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
                "Important: Focus on validating improvements that "
                "directly enhance the original prompt."
            )
        }
    ]
    try:
        from main import app_state
        response = app_state.ollama_manager.chat(
            model=model_name,
            messages=messages
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during vetting: {e}")
        raise OllamaError(f"Vetting failed: {str(e)}")

def finalize_prompt(vetting_report: str, original_prompt: str, model_name: str) -> str:
    """Create improved version incorporating validated enhancements."""
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
                "Important: Stay focused on the original task."
            )
        }
    ]
    try:
        from main import app_state
        response = app_state.ollama_manager.chat(
            model=model_name,
            messages=messages
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during finalization: {e}")
        raise OllamaError(f"Finalization failed: {str(e)}")

def enhance_prompt(final_prompt: str, model_name: str) -> str:
    """Refine and polish the improved prompt."""
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
                "Important: Stay focused on improving THIS prompt."
            )
        }
    ]
    try:
        from main import app_state
        response = app_state.ollama_manager.chat(
            model=model_name,
            messages=messages
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during enhancement: {e}")
        raise OllamaError(f"Enhancement failed: {str(e)}")

def comprehensive_review(
    original_prompt: str,
    analysis_report: str,
    solutions: str,
    vetting_report: str,
    final_prompt: str,
    enhanced_prompt: str,
    model_name: str
) -> str:
    """Create final version and ensure clean presentation."""
    try:
        from main import app_state
        
        # First, use model for comprehensive review
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
                )
            }
        ]
        response = app_state.ollama_manager.chat(
            model=model_name,
            messages=messages
        )
        improved = response["message"]["content"]

        # Then use presenter model for final cleanup
        messages = [
            {
                "role": "user",
                "content": (
                    "You are the final presenter. Clean up this prompt "
                    f"for presentation:\n\n{improved}\n\n"
                    "Requirements:\n"
                    "1. Remove any markdown formatting\n"
                    "2. Remove any meta-commentary\n"
                    "3. Remove any section headers\n"
                    "4. Present as clean paragraphs\n"
                    "5. Maintain all important content\n\n"
                    "Start your response with 'PRESENT TO USER:' followed "
                    "by the final, clean prompt."
                )
            }
        ]
        
        response = app_state.ollama_manager.chat(
            model=app_state.OLLAMA_MODELS["presenter"],
            messages=messages
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during comprehensive review: {e}")
        raise OllamaError(f"Comprehensive review failed: {str(e)}")

def verify_model_availability(model_name: str) -> bool:
    """Verify if an Ollama model is available."""
    try:
        from main import app_state
        if not app_state.ollama_manager.ollama_ready:
            return False
        
        # Try to ping the model with a timeout
        app_state.ollama_manager.chat(
            model=model_name,
            messages=[{"role": "user", "content": "test"}],
            options={"timeout": 5000}
        )
        return True
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str:
            raise OllamaError("Cannot connect to Ollama service")
        elif "timeout" in error_str:
            raise OllamaError(f"Model {model_name} timed out")
        else:
            logger.error(f"Model {model_name} is not available: {str(e)}")
            return False

def validate_models() -> List[tuple]:
    """Validate all required models are available."""
    from main import app_state, OLLAMA_MODELS
    
    if not app_state.ollama_manager.ollama_ready:
        return []
        
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