from flask import Flask, request, jsonify
from processing_functions import run_full_pipeline
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='api.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/process_prompt', methods=['POST'])
def process_prompt():
    data = request.get_json(silent=True) or {}
    prompt = (data.get('prompt') or "").strip()
    if not prompt:
        return jsonify({'error': 'prompt is required'}), 400

    logger.info(f"Received prompt: {prompt}")

    try:
        results = run_full_pipeline(prompt)
        comprehensive = results.get("comprehensive", "")

        logger.info("Prompt processed successfully")
        return jsonify({'output': comprehensive})
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
