import logging
from typing import Callable, Dict, List, Optional

from config import FALLBACK_ORDER, MODEL_CALL_TIMEOUT_MS, OLLAMA_MODELS, PROGRESS_MESSAGES
from ollama_service_manager import OllamaError

logger = logging.getLogger("prompt_enhancer")

def retry_with_fallback(func, *args, max_retries=2, model_name=None, **kwargs):
    """Retry a function with fallback models if the primary model fails."""
    last_error = None
    model_arg_index = -1

    if model_name is None:
        for i, arg in enumerate(args):
            if isinstance(arg, str) and arg in OLLAMA_MODELS.values():
                model_arg_index = i
                model_name = arg
                break
    else:
        for i, arg in enumerate(args):
            if isinstance(arg, str) and arg == model_name:
                model_arg_index = i
                break

    if model_name is None or model_arg_index == -1:
        raise ValueError("No model argument found")

    args = list(args)

    for _ in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(f"Error with model {model_name}: {e}")

    for fallback_model in FALLBACK_ORDER.get(model_name, []):
        args[model_arg_index] = fallback_model
        try:
            logger.info(f"Trying fallback model: {fallback_model}")
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(f"Error with fallback model {fallback_model}: {e}")

    raise last_error or Exception("All models failed")


def _chat(model_name: str, messages: List[Dict], options: Optional[Dict] = None) -> Dict:
    from main import app_state
    if app_state.settings_manager is None:
        from settings_manager import SettingsManager
        app_state.settings_manager = SettingsManager()
    if app_state.ollama_manager is None:
        from ollama_service_manager import OllamaServiceManager
        app_state.ollama_manager = OllamaServiceManager(app_state)

    opts = {"timeout": MODEL_CALL_TIMEOUT_MS}
    if options:
        opts.update(options)
    return app_state.ollama_manager.chat(
        model=model_name,
        messages=messages,
        options=opts
    )

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
        response = _chat(model_name, messages)
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
        response = _chat(model_name, messages)
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
        response = _chat(model_name, messages)
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
        response = _chat(model_name, messages)
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
        response = _chat(model_name, messages)
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
        response = _chat(model_name, messages)
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
        
        presenter_model = OLLAMA_MODELS.get("presenter", model_name)
        response = _chat(presenter_model, messages)
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

        _chat(model_name, [{"role": "user", "content": "test"}], options={"timeout": 5000})
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
    from main import app_state
    if app_state.settings_manager is None:
        from settings_manager import SettingsManager
        app_state.settings_manager = SettingsManager()
    if app_state.ollama_manager is None:
        from ollama_service_manager import OllamaServiceManager
        app_state.ollama_manager = OllamaServiceManager(app_state)
    
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


def _emit_progress(progress_cb: Optional[Callable], phase: str, content: Optional[str] = None) -> None:
    if progress_cb:
        progress_cb(phase, PROGRESS_MESSAGES.get(phase, ""), content)


def run_full_pipeline(prompt: str, progress_cb: Optional[Callable] = None) -> Dict[str, str]:
    """Run the full enhancement pipeline and return stage outputs."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt is empty")

    results: Dict[str, str] = {}
    _emit_progress(progress_cb, "start")

    results["analysis"] = retry_with_fallback(
        analyze_prompt, prompt, OLLAMA_MODELS["analysis"]
    )
    _emit_progress(progress_cb, "analysis_done", results["analysis"])

    results["generation"] = retry_with_fallback(
        generate_solutions, results["analysis"], OLLAMA_MODELS["generation"]
    )
    _emit_progress(progress_cb, "generation_done", results["generation"])

    results["vetting"] = retry_with_fallback(
        vet_and_refine, results["generation"], OLLAMA_MODELS["vetting"]
    )
    _emit_progress(progress_cb, "vetting_done", results["vetting"])

    results["final"] = retry_with_fallback(
        finalize_prompt, results["vetting"], prompt, OLLAMA_MODELS["finalization"]
    )
    _emit_progress(progress_cb, "finalize_done", results["final"])

    results["enhanced"] = retry_with_fallback(
        enhance_prompt, results["final"], OLLAMA_MODELS["enhancement"]
    )
    _emit_progress(progress_cb, "enhance_done", results["enhanced"])

    results["comprehensive"] = retry_with_fallback(
        comprehensive_review,
        prompt,
        results["analysis"],
        results["generation"],
        results["vetting"],
        results["final"],
        results["enhanced"],
        OLLAMA_MODELS["comprehensive"],
    )
    _emit_progress(progress_cb, "complete", results["comprehensive"])

    return results
