import logging
from typing import Any, Callable, Dict, List, Optional

from config import DEFAULT_MODE, FALLBACK_ORDER, MODEL_CALL_TIMEOUT_MS, OLLAMA_MODELS, PROGRESS_MESSAGES
from ollama_service_manager import OllamaError

logger = logging.getLogger("prompt_enhancer")

def retry_with_fallback(func: Callable, *args: Any, max_retries: int = 2, model_name: Optional[str] = None, **kwargs: Any) -> Any:
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

    args_list = list(args)

    for _ in range(max_retries):
        try:
            return func(*args_list, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(f"Error with model {model_name}: {e}")

    for fallback_model in FALLBACK_ORDER.get(model_name, []):
        args_list[model_arg_index] = fallback_model
        try:
            logger.info(f"Trying fallback model: {fallback_model}")
            return func(*args_list, **kwargs)
        except Exception as e:
            last_error = e
            logger.warning(f"Error with fallback model {fallback_model}: {e}")

    raise last_error or Exception("All models failed")

def generate_with_reflection(model_name: str, base_messages: List[Dict], options: Optional[Dict] = None) -> str:
    """Generate with self-reflection to boost weak LLMs."""
    response = _chat(model_name, base_messages, options)
    content = response["message"]["content"]

    critique_messages = base_messages + [
        {"role": "assistant", "content": content},
        {"role": "system", "content": "Critique the previous response for completeness, accuracy, clarity, structure, relevance. Identify weaknesses and suggest improvements."},
        {"role": "user", "content": "Provide critique."}
    ]
    critique = _chat(model_name, critique_messages, options)["message"]["content"]

    improve_messages = base_messages + [
        {"role": "assistant", "content": content},
        {"role": "user", "content": f"Improve using this critique: {critique}"}
    ]
    return _chat(model_name, improve_messages, options)["message"]["content"]

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

def _should_solve(prompt: str) -> bool:
    text = (prompt or "").lower()
    cues = [
        "return only",
        "output format",
        "exactly the sample output",
        "answer key",
        "final answers",
    ]
    return any(cue in text for cue in cues)

def solve_problem(prompt: str, model_name: str) -> str:
    """Solve a problem and return only the final answer."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a precise solver. Follow the problem instructions and "
                "return ONLY the final answer in the required format. Do not restate "
                "the problem and do not add explanations."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]
    try:
        response = _chat(model_name, messages, options={"temperature": 0})
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during solve: {e}")
        raise OllamaError(f"Solve failed: {str(e)}")

def verify_answer(prompt: str, answer: str, model_name: str) -> str:
    """Verify and correct the answer, returning only the final answer."""
    messages = [
        {
            "role": "system",
            "content": (
                "Verify the proposed answer against the problem. If incorrect, "
                "produce the corrected answer. Return ONLY the final answer in the "
                "required format with no explanation."
            ),
        },
        {
            "role": "user",
            "content": f"Problem:\n{prompt}\n\nProposed answer:\n{answer}",
        },
    ]
    try:
        response = _chat(model_name, messages, options={"temperature": 0})
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Error during verify: {e}")
        raise OllamaError(f"Verify failed: {str(e)}")

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


def run_full_pipeline(
    prompt: str,
    progress_cb: Optional[Callable] = None,
    mode: Optional[str] = None
) -> Dict[str, str]:
    """Run the pipeline and return stage outputs."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt is empty")

    mode = (mode or DEFAULT_MODE).lower()
    if mode == "auto" and _should_solve(prompt):
        mode = "solve"

    results: Dict[str, str] = {}
    _emit_progress(progress_cb, "start")

    if mode == "solve":
        results["solved"] = retry_with_fallback(
            solve_problem, prompt, OLLAMA_MODELS["comprehensive"]
        )
        results["comprehensive"] = retry_with_fallback(
            verify_answer,
            prompt,
            results["solved"],
            OLLAMA_MODELS.get("presenter", OLLAMA_MODELS["comprehensive"]),
        )
        _emit_progress(progress_cb, "complete", results["comprehensive"])
        return results

    if mode == "boost":
        """Boost mode: Use reflection to increase intelligence of weak LLMs"""
        boost_model = "mistral:latest"

        def safe_generate(prompt_text: str) -> str:
            msgs = [{"role": "user", "content": prompt_text}]
            try:
                return generate_with_reflection(boost_model, msgs)
            except Exception as e:
                logger.warning(f"Boost reflection failed: {e}")
                return _chat(boost_model, msgs)["message"]["content"]

        # Analysis stage
        analysis_text = f"""Analyze this prompt: '{prompt}'

Focus on:
1. Core requirements and goals
2. Key components needed
3. Specific constraints or parameters
4. Expected output format
5. Quality criteria

Provide a clear, focused analysis that will help in improving this exact prompt."""
        results["analysis"] = safe_generate(analysis_text)
        _emit_progress(progress_cb, "analysis_done", results["analysis"])

        # Generation stage
        gen_text = f"""Based on this analysis: '{results["analysis"]}'

Generate specific improvements that:
1. Address identified issues
2. Enhance clarity and specificity
3. Add necessary structure
4. Maintain focus on core goals
5. Consider all quality criteria

Important: Generate practical, focused improvements that directly enhance the prompt."""
        results["generation"] = safe_generate(gen_text)
        _emit_progress(progress_cb, "generation_done", results["generation"])

        # Vetting stage
        vet_text = f"""Review these suggested improvements: '{results["generation"]}'

Evaluate how well they enhance the original prompt:
1. Do they address core requirements?
2. Are they clear and specific?
3. Do they maintain focus on the task?
4. Are they practical and implementable?

Focus on validating improvements that directly enhance the original prompt."""
        results["vetting"] = safe_generate(vet_text)
        _emit_progress(progress_cb, "vetting_done", results["vetting"])

        # Finalize stage
        final_text = f"""Original Prompt: {prompt}
Validated Improvements: {results["vetting"]}

Create an improved version that:
1. Maintains the original goal
2. Incorporates validated improvements
3. Uses clear, specific language
4. Adds necessary structure
5. Includes any required constraints

Stay focused on the original task."""
        results["final"] = safe_generate(final_text)
        _emit_progress(progress_cb, "finalize_done", results["final"])

        # Enhance stage
        enhance_text = f"""Polish and refine this prompt:

{results["final"]}

Focus on:
1. Making instructions crystal clear
2. Adding any missing details
3. Improving structure
4. Ensuring completeness
5. Maintaining focus

Stay focused on improving THIS prompt."""
        results["enhanced"] = safe_generate(enhance_text)
        _emit_progress(progress_cb, "enhance_done", results["enhanced"])

        # Comprehensive review
        comp_text = f"""Review all versions and create refined prompt:
Original: {prompt}
Analysis: {results["analysis"]}
Generation: {results["generation"]}
Vetting: {results["vetting"]}
Final: {results["final"]}
Enhanced: {results["enhanced"]}

Combine best elements for maximum clarity and effectiveness."""
        results["comprehensive"] = safe_generate(comp_text)
        _emit_progress(progress_cb, "complete", results["comprehensive"])
        return results

    # Original pipeline
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
