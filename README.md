![Banner](banner.png)

# Logic Filter

A GUI application that analyzes, improves, and refines prompts using a
multi-model approach.

## Features

- Interactive GUI interface with input and output areas
- Four-phase prompt processing:
  1. Analysis (using `llama3.2:latest`)
  2. Solution Generation (using `olmo2:13b`)
  3. Vetting and Screening (using `deepseek-r1`)
  4. Final Prompt Creation (using `deepseek-r1:14b`)
- Real-time progress updates
- Detailed output for each processing phase

## Requirements

- Python 3.x
- Ollama
- Required Python packages (install via pip):

  ```
  pip install -r requirements.txt
  ```

## Setup

1. Ensure Ollama is installed and running.
2. Pull the required models:

   ```
   ollama pull llama3.2:latest
   ollama pull olmo2:13b
   ollama pull deepseek-r1
   ollama pull deepseek-r1:14b
   ```

3. Install the Python dependencies:

   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:

   ```
   python LogicFilter.py
   ```

2. Enter your prompt in the input text box.
3. Click "Process & Improve Prompt".
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

## Tests

Mocked pipeline smoke test (no Ollama required):

```
python3 -m unittest -v tests.test_pipeline
```

Full test run in venv:

```
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
```

## How It Works

The application uses a four-phase process with specialized models:

1. **Analysis Phase (`llama3.2:latest`)**

   - Breaks down the prompt.
   - Identifies potential issues, assumptions, and ambiguities.
   - Analyzes structure and components.

2. **Generation Phase (`olmo2:13b`)**

   - Creates multiple alternative versions of the prompt.
   - Explores different approaches and phrasings.
   - Generates creative solutions.

3. **Vetting Phase (`deepseek-r1`)**

   - Evaluates all generated solutions.
   - Identifies and reports on weaknesses, inconsistencies, and missing
     elements.
   - Suggests specific areas for expansion and enhancement.

4. **Finalization Phase (`deepseek-r1:14b`)**
   - Takes the original prompt and the vetting report.
   - Creates a final, improved, and expanded "super prompt".
   - Addresses all identified issues and incorporates expansion opportunities.
   - Follows best practices for prompt engineering, including:
     - Clear, precise instructions at the beginning.
     - Specific details about context, outcome, length, format, and style.
     - Use of appropriate leading words or phrases.
     - Avoiding vague or imprecise language.
     - Providing positive guidance ("what to do" instead of just "what not to
       do").

Progress is shown in real-time with clear indicators for each phase.
