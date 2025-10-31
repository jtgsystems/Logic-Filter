from flask import Flask, request, jsonify
from processing_functions import (
    analyze_prompt,
    generate_solutions,
    vet_and_refine,
    finalize_prompt,
    enhance_prompt,
    comprehensive_review
)
from config import OLLAMA_MODELS
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='api.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/process_prompt', methods=['POST'])
def process_prompt():
    data = request.get_json()
    prompt = data['prompt']

    logger.info(f"Received prompt: {prompt}")

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
        return jsonify({'output': comprehensive})
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)