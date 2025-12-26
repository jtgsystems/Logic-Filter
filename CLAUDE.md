# Logic Filter - Claude Code Reference Guide

**A multi-model AI prompt enhancement application using Ollama for intelligent prompt analysis, improvement, and refinement.**

---

## Project Overview

Logic Filter is a sophisticated prompt engineering tool that processes user prompts through a six-phase AI pipeline to generate enhanced, production-ready prompts. The application leverages multiple specialized Ollama models, each optimized for specific enhancement tasks.

### Core Purpose
- Analyze user-provided prompts for weaknesses and improvement opportunities
- Generate multiple alternative prompt formulations
- Vet and validate improvements through specialized models
- Produce polished, professional-grade prompts
- Provide both GUI (customtkinter) and API (Flask) interfaces

### Key Features
- **Multi-Phase Processing**: 6-stage pipeline with specialized models
- **Dual Interface**: Desktop GUI and REST API
- **Real-time Progress**: Visual indicators and progress tracking
- **Processing History**: Undo/redo with persistent history
- **Model Indicators**: Live status of active AI models
- **Theme Support**: Light/dark mode with customtkinter
- **Memory Monitoring**: Real-time memory usage tracking
- **Fallback System**: Automatic model fallback on failures

---

## Architecture Overview

### Application Structure

```
Logic-Filter/
├── main.py                      # Main entry point, GUI setup
├── LogicFilter.py               # Monolithic GUI implementation (legacy)
├── api.py                       # Flask REST API server
├── processing_functions.py      # Core AI processing pipeline
├── ui_components.py             # UI widgets and components
├── ollama_service_manager.py    # Ollama service integration
├── settings_manager.py          # Settings persistence
├── processing_history.py        # History management with undo/redo
├── test_api.py                  # API unit tests
├── settings.json                # User preferences and configuration
├── requirements.txt             # Python dependencies
├── Meta-Prompt Template.md      # Prompt engineering guidelines
├── banner.png                   # Application banner
├── tailwind_ui/
│   └── index.html              # Web-based UI (Tailwind CSS)
└── .vscode/
    └── launch.json             # VS Code debugging config
```

### Component Relationships

```
main.py (Entry Point)
    ├── ApplicationState (Global state manager)
    ├── OllamaServiceManager (AI service wrapper)
    ├── SettingsManager (Configuration)
    ├── ProcessingHistory (Undo/redo)
    ├── UI Components (customtkinter)
    └── Processing Functions (AI pipeline)

api.py (Flask Server)
    └── Processing Functions (Same AI pipeline)
```

---

## Technology Stack

### Core Dependencies

**Python Frameworks:**
- **customtkinter** - Modern Tkinter UI framework with native dark mode
- **Flask** (≥3.1.2) - Lightweight web framework for REST API
- **Rich** - Terminal logging and formatting
- **psutil** - System resource monitoring

**AI Integration:**
- **Ollama** - Local LLM inference engine (via HTTP + Python SDK)
- **requests** - HTTP client for Ollama health checks

**Testing:**
- **pytest** - Unit and integration testing framework

### Python Version
- **Python 3.x** (3.8+ recommended)

### External Services
- **Ollama Server** - Must be running on `localhost:11434`
- **Required Models** (configurable in settings.json):
  - `llama3.2:latest` - Analysis phase
  - `olmo2:13b` - Solution generation
  - `deepseek-r1` - Vetting
  - `deepseek-r1:14b` - Finalization and presentation
  - `phi4:latest` - Enhancement and comprehensive review

---

## Directory Structure Details

### Root Files

**main.py** (Current implementation)
- Modern modular architecture
- ApplicationState pattern for global state
- Threading for async processing
- Integrated Flask API server

**LogicFilter.py** (Legacy monolithic)
- Single-file implementation
- Contains duplicate classes/functions
- Kept for backward compatibility

**api.py**
- Flask REST API endpoint: `/process_prompt`
- JSON input/output
- Logging to `api.log`
- Shares processing functions with GUI

**processing_functions.py**
- Six core processing functions:
  1. `analyze_prompt()` - Initial analysis
  2. `generate_solutions()` - Alternative generation
  3. `vet_and_refine()` - Validation
  4. `finalize_prompt()` - Initial improvement
  5. `enhance_prompt()` - Polishing
  6. `comprehensive_review()` - Final cleanup
- Model verification and fallback logic
- Thread-safe Ollama integration

**ui_components.py**
- StatusBar with theme toggle
- LoadingIndicator with progress animation
- Toolbar with action buttons
- Model indicator widgets
- Text sanitization and output formatting

**ollama_service_manager.py**
- Health check monitoring
- Service initialization
- Model availability verification
- Chat wrapper with error handling
- Periodic status checks (30-second interval)

**settings_manager.py**
- JSON-based settings persistence
- Default settings with merge logic
- Window state management
- Auto-save support

**processing_history.py**
- Thread-safe history management
- Undo/redo functionality (50-entry max)
- Timestamp tracking
- JSON export capability

### Configuration Files

**settings.json**
```json
{
  "theme": "dark",
  "font_size": 14,
  "max_history": 50,
  "autosave": true,
  "show_model_indicators": true,
  "save_window_state": true,
  "default_models": {
    "analysis": "llama3.2:latest",
    "generation": "olmo2:13b",
    "vetting": "deepseek-r1",
    "finalization": "deepseek-r1:14b",
    "enhancement": "phi4:latest",
    "comprehensive": "phi4:latest",
    "presenter": "deepseek-r1:14b"
  },
  "window": {
    "geometry": "1024x768+714+78",
    "zoomed": false
  }
}
```

**requirements.txt**
```
Flask
customtkinter
rich
psutil
pytest
```

---

## Development Workflow

### Setup Instructions

1. **Install Ollama**
   ```bash
   # Install from https://ollama.ai
   # Verify installation
   ollama --version
   ```

2. **Pull Required Models**
   ```bash
   ollama pull llama3.2:latest
   ollama pull olmo2:13b
   ollama pull deepseek-r1
   ollama pull deepseek-r1:14b
   ollama pull phi4:latest
   ```

3. **Create Python Virtual Environment**
   ```bash
   cd Logic-Filter
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install ollama  # Not in requirements.txt but required
   ```

5. **Verify Ollama Service**
   ```bash
   # Should be running on localhost:11434
   curl http://localhost:11434/api/health
   ```

### Running the Application

**GUI Application (Desktop)**
```bash
python main.py
# OR legacy version:
python LogicFilter.py
```

**API Server Only**
```bash
python api.py
# Runs on http://localhost:5000
```

**API Usage Example**
```bash
curl -X POST http://localhost:5000/process_prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a function to parse JSON"}'
```

**Web UI (Tailwind)**
```bash
# Open in browser
firefox tailwind_ui/index.html
# Note: Requires API server running
```

### Development Commands

**Run Tests**
```bash
pytest test_api.py
pytest  # Run all tests
```

**Check Code Style**
```bash
# Install linting tools (optional)
pip install black flake8
black *.py
flake8 *.py
```

**Monitor Logs**
```bash
tail -f api.log
```

---

## Processing Pipeline Details

### Six-Phase Enhancement Process

**Phase 1: Analysis (`llama3.2:latest`)**
- Identifies core requirements and goals
- Analyzes key components needed
- Detects constraints and parameters
- Defines expected output format
- Establishes quality criteria

**Phase 2: Generation (`olmo2:13b`)**
- Creates alternative prompt formulations
- Explores different approaches
- Enhances clarity and specificity
- Adds necessary structure
- Maintains focus on core goals

**Phase 3: Vetting (`deepseek-r1`)**
- Validates suggested improvements
- Checks clarity and specificity
- Ensures focus maintenance
- Confirms practicality
- Flags off-topic suggestions

**Phase 4: Finalization (`deepseek-r1:14b`)**
- Merges original prompt with improvements
- Maintains original intent
- Uses clear, specific language
- Adds necessary structure
- Incorporates constraints

**Phase 5: Enhancement (`phi4:latest`)**
- Polishes instructions for clarity
- Adds missing details (targets 10+ improvements)
- Improves structural organization
- Ensures completeness
- Maintains focus throughout

**Phase 6: Comprehensive Review (`phi4:latest` + `deepseek-r1:14b`)**
- Reviews all previous versions
- Combines best elements
- Final cleanup and presentation
- Removes markdown formatting
- Strips meta-commentary

### Model Fallback Strategy

**Fallback Order (defined in LogicFilter.py)**
```python
FALLBACK_ORDER = {
    "llama3.2:latest": ["deepseek-r1", "phi4:latest"],
    "olmo2:13b": ["deepseek-r1:14b", "phi4:latest"],
    "deepseek-r1": ["phi4:latest", "llama3.2:latest"],
    "deepseek-r1:14b": ["phi4:latest", "deepseek-r1"],
    "phi4:latest": ["deepseek-r1:14b", "llama3.2:latest"]
}
```

**Retry Logic**
- Max 3 retries per model
- Automatic fallback on failure
- Connection error detection
- Timeout handling (5 seconds for verification)

---

## Configuration and Settings

### Customization Options

**Theme Configuration**
- Dark mode (default)
- Light mode
- Toggle via status bar button
- Persists across sessions

**Model Configuration**
- Edit `settings.json` > `default_models`
- Restart application to apply
- Verify models exist in Ollama

**Window State**
- Auto-save geometry and position
- Restore on next launch
- Configurable via `save_window_state`

**History Settings**
- Max history: 50 entries (default)
- Configurable via `max_history`
- Thread-safe operations
- JSON export for backup

**Performance Tuning**
```json
{
  "request_timeout": 2,          // Ollama health check timeout
  "check_interval": 30000,       // Service check interval (ms)
  "memory_update_interval": 15000 // Memory monitoring (ms)
}
```

---

## Testing Approach

### Unit Tests (test_api.py)

**Current Coverage**
- API endpoint functionality
- JSON request/response validation
- Basic integration with processing functions

**Test Execution**
```bash
pytest test_api.py -v
pytest --cov=. test_api.py  # With coverage
```

### Manual Testing Checklist

**GUI Testing**
- [ ] Launch application without errors
- [ ] Process a simple prompt
- [ ] Verify all 6 phases complete
- [ ] Check model indicators update
- [ ] Test theme toggle
- [ ] Verify memory monitoring
- [ ] Test undo/redo (if implemented)
- [ ] Export history to JSON
- [ ] Save output to file

**API Testing**
```bash
# Valid request
curl -X POST http://localhost:5000/process_prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# Should return {"output": "..."}
```

**Ollama Integration**
- [ ] Service auto-detection works
- [ ] Health checks succeed
- [ ] Model verification succeeds
- [ ] Fallback models activate on failure
- [ ] Connection errors handled gracefully

---

## Performance Considerations

### Memory Management

**Monitoring**
- psutil tracks application memory
- Updates every 15 seconds
- Displayed in status bar
- Typical usage: 50-150MB

**Optimization Tips**
- Limit history to 50 entries
- Clear history periodically
- Close unused models in Ollama
- Use smaller models for testing

### Threading

**GUI Thread**
- Main tkinter event loop
- UI updates and rendering
- User input handling

**Processing Thread**
- Spawned for each prompt processing
- Daemon thread (auto-terminates)
- Prevents GUI freezing
- Thread-safe history updates

**Flask Thread** (when running main.py)
- Separate daemon thread
- Runs API server concurrently
- Debug mode disabled for threading

### Ollama Performance

**Service Checks**
- Throttled to 30-second intervals
- Only checks when not connected
- 2-second timeout for health checks
- Reduces overhead on system

**Model Loading**
- First inference loads model into memory
- Subsequent calls use cached model
- ~2-30 seconds initial load time
- Depends on model size (13B models slower)

---

## Known Issues and Troubleshooting

### Common Issues

**Issue 1: "Ollama service not ready"**
- **Cause**: Ollama not running
- **Solution**:
  ```bash
  # Start Ollama
  ollama serve
  # OR systemd service
  systemctl start ollama
  ```

**Issue 2: Model not found**
- **Cause**: Model not pulled
- **Solution**:
  ```bash
  ollama list  # Check installed models
  ollama pull llama3.2:latest
  ```

**Issue 3: Processing hangs**
- **Cause**: Model timeout or out of memory
- **Solution**:
  - Restart Ollama service
  - Free system memory
  - Use smaller models (7B instead of 13B)

**Issue 4: GUI doesn't start**
- **Cause**: customtkinter not installed or assets missing
- **Solution**:
  ```bash
  pip install customtkinter
  # Creates assets/ directory automatically
  ```

**Issue 5: API returns 500 error**
- **Cause**: Processing function failure
- **Solution**:
  - Check `api.log` for details
  - Verify Ollama connection
  - Test models individually

### Debugging Tips

**Enable Verbose Logging**
```python
# In main.py or LogicFilter.py
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
```

**Test Ollama Connection**
```bash
curl http://localhost:11434/api/health
ollama list
ollama run llama3.2:latest "test"
```

**Check Model Status**
```bash
# Monitor Ollama logs
journalctl -u ollama -f
# OR
tail -f ~/.ollama/logs/ollama.log
```

---

## Next Steps and Roadmap

### Short-Term Improvements

**Code Quality**
- [ ] Remove duplicate code in LogicFilter.py
- [ ] Add type hints throughout
- [ ] Increase test coverage to >80%
- [ ] Add integration tests for full pipeline
- [ ] Document all functions with docstrings

**Features**
- [ ] Implement undo/redo in GUI
- [ ] Add batch processing mode
- [ ] Create preset prompt templates
- [ ] Export to multiple formats (PDF, Markdown)
- [ ] Add prompt comparison view

**UI/UX**
- [ ] Improve error messages
- [ ] Add keyboard shortcuts
- [ ] Implement drag-and-drop file support
- [ ] Create settings dialog
- [ ] Add tutorial/onboarding

### Long-Term Vision

**Multi-Model Support**
- [ ] Support for OpenAI API
- [ ] Integration with Claude API
- [ ] Gemini API support
- [ ] Model performance comparison

**Advanced Features**
- [ ] Prompt versioning and branching
- [ ] Collaborative editing
- [ ] Cloud sync for history
- [ ] Custom model training
- [ ] Prompt marketplace/sharing

**Infrastructure**
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Automated testing
- [ ] Performance benchmarking
- [ ] Documentation site

---

## Development Notes

### Code Organization Best Practices

**When to Edit main.py vs LogicFilter.py**
- **main.py**: Use for new features (modular architecture)
- **LogicFilter.py**: Legacy support only (avoid changes)

**Adding New Processing Phases**
1. Create function in `processing_functions.py`
2. Add model to `settings.json` > `default_models`
3. Update `OLLAMA_MODELS` dict in main.py
4. Add progress message to `PROGRESS_MESSAGES`
5. Call from `process_prompt()` thread

**Adding UI Components**
1. Define class in `ui_components.py`
2. Import in main.py
3. Instantiate in `setup_main_window()`
4. Register with `app_state` if needed

### Git Workflow

**Branching Strategy**
```bash
git checkout -b feature/new-enhancement
# Make changes
git add .
git commit -m "Add new enhancement feature"
git push origin feature/new-enhancement
# Create PR on GitHub
```

**Commit Message Format**
```
<type>: <subject>

<body>

Types: feat, fix, docs, style, refactor, test, chore
```

---

## Meta-Prompt Engineering Reference

See `Meta-Prompt Template.md` for comprehensive prompt engineering guidelines including:
- Task description framework
- Goals and constraints definition
- Example-driven prompting
- Taxonomy of prompting strategies
- Model capability considerations
- Evaluation metrics
- Optimization techniques
- Iterative refinement process

---

## Additional Resources

### Documentation
- **Ollama Docs**: https://ollama.ai/docs
- **customtkinter Docs**: https://customtkinter.tomschimansky.com/
- **Flask Docs**: https://flask.palletsprojects.com/

### Related Projects
- Original concept inspired by multi-agent prompt refinement
- Uses Meta-Prompt Template methodology
- Follows best practices from prompt engineering research

---

## Project Status

**Current Version**: 1.0 (inferred, no version file)
**Maintenance**: Active development
**License**: Not specified
**Repository**: https://github.com/jtgsystems/Logic-Filter

---

**Last Updated**: 2025-10-26
**Claude Code Documentation Generated**: Automated analysis and documentation

## Framework Versions

- **Flask**: Flask

