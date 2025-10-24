import logging
import os

from flask import Flask, jsonify, request

from main import OLLAMA_MODELS
from processing_functions import (
    analyze_prompt,
    comprehensive_review,
    enhance_prompt,
    finalize_prompt,
    generate_solutions,
    vet_and_refine,
)

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Maximum prompt length for security
MAX_PROMPT_LENGTH = 50000


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@app.route('/process_prompt', methods=['POST'])
def process_prompt():
    """Process a prompt through the enhancement pipeline."""
    # Input validation
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    if 'prompt' not in data:
        return jsonify({'error': 'Missing required field: prompt'}), 400

    prompt = data['prompt']

    # Validate prompt
    if not isinstance(prompt, str):
        return jsonify({'error': 'Prompt must be a string'}), 400

    if not prompt.strip():
        return jsonify({'error': 'Prompt cannot be empty'}), 400

    if len(prompt) > MAX_PROMPT_LENGTH:
        return jsonify({
            'error': f'Prompt too long (max {MAX_PROMPT_LENGTH} characters)'
        }), 400

    logger.info(f"Received prompt (length: {len(prompt)})")

    try:
        analysis = analyze_prompt(prompt, OLLAMA_MODELS["analysis"])
        solutions = generate_solutions(analysis, OLLAMA_MODELS["generation"])
        vetted = vet_and_refine(solutions, OLLAMA_MODELS["vetting"])
        final = finalize_prompt(vetted, prompt, OLLAMA_MODELS["finalization"])
        enhanced = enhance_prompt(final, OLLAMA_MODELS["enhancement"])
        comprehensive = comprehensive_review(
            prompt, analysis, solutions, vetted,
            final, enhanced, OLLAMA_MODELS["comprehensive"]
        )

        logger.info("Prompt processed successfully")
        return jsonify({'output': comprehensive}), 200
    except Exception as e:
        logger.error(f"Error processing prompt: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Never run with debug=True in production
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)
