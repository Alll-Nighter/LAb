@echo off
REM run_llm.bat - Start the LLM Service (FastAPI + Ollama) on port 8001
REM Run from the smart-lab-safety project root directory.

cd /d "%~dp0\.."

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Starting LLM Service on http://0.0.0.0:8001
echo Make sure Ollama is running on http://localhost:11434 with llama3.2 model pulled.

uvicorn llm_service.main:app --host 0.0.0.0 --port 8001 --reload