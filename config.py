import os
import json


def _load_env_json(key, default):
    raw = os.getenv(key, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


OLLAMA_MODELS = _load_env_json(
    "LOGIC_FILTER_MODELS_JSON",
    {
        "analysis": "llama3.2:latest",
        "generation": "olmo2:13b",
        "vetting": "deepseek-r1",
        "finalization": "deepseek-r1:14b",
        "enhancement": "phi4:latest",
        "comprehensive": "phi4:latest",
        "presenter": "deepseek-r1:14b",
    },
)

FALLBACK_ORDER = _load_env_json(
    "LOGIC_FILTER_FALLBACK_JSON",
    {
        "llama3.2:latest": ["deepseek-r1", "phi4:latest"],
        "olmo2:13b": ["deepseek-r1:14b", "phi4:latest"],
        "deepseek-r1": ["phi4:latest", "llama3.2:latest"],
        "deepseek-r1:14b": ["phi4:latest", "deepseek-r1"],
        "phi4:latest": ["deepseek-r1:14b", "llama3.2:latest"],
    },
)

PROGRESS_MESSAGES = {
    "start": "Processing prompt...\n",
    "analyzing": "Phase 1/6: Analysis\n",
    "analysis_done": "Analysis complete.\n\n",
    "generating": "Phase 2/6: Generation\n",
    "generation_done": "Generation complete.\n\n",
    "vetting": "Phase 3/6: Vetting\n",
    "vetting_done": "Vetting complete.\n\n",
    "finalizing": "Phase 4/6: Finalization\n",
    "finalize_done": "Finalization complete.\n\n",
    "enhancing": "Phase 5/6: Enhancement\n",
    "enhance_done": "Enhancement complete.\n\n",
    "comprehensive": "Phase 6/6: Review\n",
    "complete": "Process complete.\n\n",
}

REQUEST_TIMEOUT_SEC = int(os.getenv("LOGIC_FILTER_REQUEST_TIMEOUT_SEC", "20"))
MODEL_CALL_TIMEOUT_MS = int(os.getenv("LOGIC_FILTER_MODEL_TIMEOUT_MS", "120000"))
