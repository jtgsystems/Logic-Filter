# Logic Filter

A GUI application that analyzes, improves, and refines prompts using a
multi-model approach.

## Features

- Interactive GUI interface with input and output areas
- Three-phase prompt processing:
  1. Analysis (using llama3.2:latest)
  2. Solution Generation (using olmo2:13b)
  3. Refinement and Improvement (using phi4:latest)
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

1. Ensure Ollama is installed and running
2. Pull the required models:

   ```
   ollama pull llama3.2:latest
   ollama pull olmo2:13b
   ollama pull phi4:latest
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

2. Enter your prompt in the input text box
3. Click "Process & Improve Prompt"
4. The application will:
   - Analyze your prompt for potential issues
   - Generate alternative approaches
   - Refine and improve the final version
5. View the results in the output area, including:
   - Initial analysis
   - Generated alternatives
   - Final improved version

## How It Works

The application uses three specialized models in sequence:

1. **Analysis Phase (llama3.2:latest)**

   - Breaks down the prompt
   - Identifies potential issues
   - Analyzes structure and components

2. **Generation Phase (olmo2:13b)**

   - Creates multiple alternative versions
   - Explores different approaches
   - Generates creative solutions

3. **Refinement Phase (phi4:latest)**
   - Evaluates all versions
   - Identifies and fixes issues
   - Produces the final improved prompt

Progress is shown in real-time with clear indicators for each phase.
