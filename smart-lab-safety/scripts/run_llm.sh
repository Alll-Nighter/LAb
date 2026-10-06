#!/usr/bin/env bash
# run_llm.sh - Start the LLM Service (FastAPI + Ollama) on port 8001
# Run from the smart-lab-safety project root directory.

set -euo pipefail

# Ensure we are in the correct directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting LLM Service on http://0.0.0.0:8001"
echo "Make sure Ollama is running on http://localhost:11434 with llama3.2 model pulled."

exec uvicorn llm_service.main:app --host 0.0.0.0 --port 8001 --reload