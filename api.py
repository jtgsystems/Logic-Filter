"""
Flask API for Logic Filter prompt enhancement.
Provides REST endpoint for processing prompts through the AI pipeline.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS with security settings
CORS(app, resources={
    r"/process_prompt": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Ollama model configuration (separated to avoid circular imports)
OLLAMA_MODELS = {
    "analysis": "llama3.2:latest",
    "generation": "olmo2:13b",
    "vetting": "deepseek-r1",
    "finalization": "deepseek-r1:14b",
    "enhancement": "phi4:latest",
    "comprehensive": "phi4:latest",
    "presenter": "deepseek-r1:14b",
}


def validate_prompt_request(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate incoming prompt request data.

    Args:
        data: Request JSON data

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data:
        return False, "No JSON data provided"

    if 'prompt' not in data:
        return False, "Missing 'prompt' field in request"

    prompt = data['prompt']

    if not isinstance(prompt, str):
        return False, "'prompt' must be a string"

    if not prompt.strip():
        return False, "'prompt' cannot be empty"

    if len(prompt) > 50000:  # 50KB limit
        return False, "'prompt' exceeds maximum length of 50,000 characters"

    return True, ""


@app.route('/process_prompt', methods=['POST'])
def process_prompt():
    """
    Process a prompt through the AI enhancement pipeline.

    Expected JSON payload:
        {
            "prompt": "string (required, max 50,000 chars)"
        }

    Returns:
        Success: {"output": "enhanced_prompt"}
        Error: {"error": "error_message"}, HTTP 400/500
    """
    try:
        data = request.get_json(silent=True)

        # Validate request
        is_valid, error_msg = validate_prompt_request(data)
        if not is_valid:
            logger.warning(f"Invalid request: {error_msg}")
            return jsonify({'error': error_msg}), 400

        prompt = data['prompt'].strip()
        logger.info(f"Processing prompt (length: {len(prompt)})")

        # Import processing functions here to avoid circular imports
        from processing_functions import (
            analyze_prompt,
            generate_solutions,
            vet_and_refine,
            finalize_prompt,
            enhance_prompt,
            comprehensive_review
        )

        # Process through pipeline
        analysis = analyze_prompt(prompt, OLLAMA_MODELS["analysis"])
        solutions = generate_solutions(analysis, OLLAMA_MODELS["generation"])
        vetted = vet_and_refine(solutions, OLLAMA_MODELS["vetting"])
        final = finalize_prompt(vetted, prompt, OLLAMA_MODELS["finalization"])
        enhanced = enhance_prompt(final, OLLAMA_MODELS["enhancement"])
        comprehensive = comprehensive_review(
            prompt, analysis, solutions, vetted,
            final, enhanced, OLLAMA_MODELS["comprehensive"],
            OLLAMA_MODELS["presenter"]
        )

        logger.info("Prompt processed successfully")
        return jsonify({'output': comprehensive, 'status': 'success'}), 200

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({'error': 'Server configuration error'}), 500

    except Exception as e:
        logger.error(f"Error processing prompt: {e}", exc_info=True)
        # Don't expose internal error details in production
        return jsonify({'error': 'An error occurred while processing your prompt'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({'status': 'healthy', 'service': 'logic-filter-api'}), 200


if __name__ == '__main__':
    import os
    # Only use debug mode in development
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)