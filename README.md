![Banner](banner.png)

# Logic Filter

A GUI application that analyzes, improves, and refines prompts using a
multi-model approach.

## Features

- Interactive GUI interface with input and output areas
- Six-phase prompt processing pipeline:
  1. Analysis (using `llama3.2:latest`)
  2. Solution Generation (using `olmo2:13b`)
  3. Vetting and Screening (using `deepseek-r1`)
  4. Finalization (using `deepseek-r1:14b`)
  5. Enhancement (using `phi4:latest`)
  6. Comprehensive Review (using `phi4:latest`)
- REST API for programmatic access
- Real-time progress updates
- Detailed output for each processing phase
- Processing history with undo/redo
- Customizable settings

## Requirements

- Python 3.9+
- Ollama
- Required Python packages (install via pip)

## Setup

1. Ensure Ollama is installed and running.
2. Pull the required models:

   ```bash
   ollama pull llama3.2:latest
   ollama pull olmo2:13b
   ollama pull deepseek-r1
   ollama pull deepseek-r1:14b
   ollama pull phi4:latest
   ```

3. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### GUI Application

1. Run the GUI application:

   ```bash
   python main.py
   ```

2. Enter your prompt in the input text box.
3. Click "Process Prompt".
4. The application will:
   - Analyze your prompt for potential issues.
   - Generate alternative approaches.
   - Vet and screen the generated solutions.
   - Create a final, improved "super prompt" based on the vetting report and
     incorporating best practices for prompt engineering.
5. View the results in the output area, including:
   - Initial analysis
   - Generated alternatives
   - Vetting report
   - Final improved version

### REST API

The application also includes a REST API that runs automatically when you start the GUI.

**Process a prompt:**
```bash
curl -X POST http://127.0.0.1:5000/process_prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your prompt here"}'
```

**Health check:**
```bash
curl http://127.0.0.1:5000/health
```

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Code Quality

The project uses ruff for linting and mypy for type checking:

```bash
# Run linter
ruff check .

# Fix auto-fixable issues
ruff check . --fix

# Run type checker
mypy .
```

## Project Structure

```
Logic-Filter/
├── main.py                    # Main GUI application entry point
├── api.py                     # Flask REST API
├── processing_functions.py    # Core prompt processing logic
├── ui_components.py          # GUI components
├── ollama_service_manager.py # Ollama service integration
├── settings_manager.py       # Application settings
├── processing_history.py     # History and undo/redo functionality
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
├── .gitignore               # Git ignore rules
└── tests/                   # Test suite
    ├── test_settings_manager.py
    ├── test_processing_history.py
    ├── test_ui_components.py
    └── test_api.py
```

## How It Works

The application uses a six-phase process with specialized models:

1. **Analysis Phase (`llama3.2:latest`)**
   - Breaks down the prompt
   - Identifies potential issues, assumptions, and ambiguities
   - Analyzes structure and components

2. **Generation Phase (`olmo2:13b`)**
   - Creates multiple alternative versions of the prompt
   - Explores different approaches and phrasings
   - Generates creative solutions

3. **Vetting Phase (`deepseek-r1`)**
   - Evaluates all generated solutions
   - Identifies and reports on weaknesses, inconsistencies, and missing elements
   - Suggests specific areas for expansion and enhancement

4. **Finalization Phase (`deepseek-r1:14b`)**
   - Takes the original prompt and the vetting report
   - Creates an improved and expanded version
   - Addresses all identified issues and incorporates expansion opportunities

5. **Enhancement Phase (`phi4:latest`)**
   - Refines and polishes the improved prompt
   - Adds any missing details
   - Improves structure and clarity
   - Ensures completeness

6. **Comprehensive Review Phase (`phi4:latest`)**
   - Reviews all versions and creates a final refined prompt
   - Combines the best elements from all phases
   - Ensures clean presentation and maximum effectiveness

The application follows best practices for prompt engineering:
- Clear, precise instructions
- Specific details about context, outcome, length, format, and style
- Appropriate leading words or phrases
- Avoidance of vague or imprecise language
- Positive guidance (what to do, not just what to avoid)

Progress is shown in real-time with clear indicators for each phase.
