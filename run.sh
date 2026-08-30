#!/bin/bash
set -e

echo "======================================================================="
echo "                 LEMMA APPLICATION SETUP AND DEVELOPMENT RUNNER"
echo "======================================================================="
echo ""

cd "$(dirname "$0")"

# 1. Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.10+ and try again."
    exit 1
fi

python_version=$(python3 --version | cut -d' ' -f2)
echo "[INFO] Found Python 3: $python_version"

# 2. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "[INFO] Creating Python virtual environment [venv]..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
else
    echo "[INFO] Virtual environment [venv] already exists."
fi

# 3. Activate venv and install requirements
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo "[INFO] Installing/Upgrading python dependencies from backend/requirements.txt..."
pip install --upgrade pip
pip install -r backend/requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install pip requirements."
    exit 1
fi

# 4. Install spaCy English Model
echo "[INFO] Checking and downloading spaCy English tokenizer model..."
python -m spacy download en_core_web_sm
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to download spaCy model."
    exit 1
fi

# 5. Run Backend Server
echo ""
echo "======================================================================="
echo "          SUCCESS: Setup complete. Starting Uvicorn development server..."
echo "          You can access the client UI at: http://localhost:8000"
echo "          You can view API swagger docs at: http://localhost:8000/docs"
echo "======================================================================="
echo ""

export PYTHONPATH=backend
python -m uvicorn app.main:app --reload --port 8000
