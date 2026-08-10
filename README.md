# Lemma: Local-First Plagiarism Analysis & Academic Text Rewriting Platform

![Lemma Header](https://img.shields.io/badge/Lemma-v1.1.0-blueviolet?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=for-the-badge&logo=ollama)
![PyTest](https://img.shields.io/badge/Tests-Passing-brightgreen?style=for-the-badge&logo=pytest)

**Lemma** is a high-performance, local-first **Plagiarism Analysis, Document Analytics, and Generative Academic Text Rewriting Platform**. Built with a decoupled client-server architecture, local vector NLP pipelines, asynchronous Celery worker queues, and publication-grade PDF report automation, Lemma enables researchers, students, and educators to analyze document integrity and eliminate plagiarized segments while maintaining total privacy.

---

## 🌟 Key Features

* 🔬 **Dual-Tier Plagiarism Engine**: Combines classical lexical matching (**TF-IDF + Cosine Similarity**) with deep vector semantic indexing (**Sentence-Transformers + local FAISS / Postgres pgvector / Elasticsearch**) to detect verbatim copy-pastes as well as complex structural paraphrasing.
* 📍 **Precision Coordinate Mapping**: Utilizes an optimized `spaCy` tokenization pipeline to segment documents into sentences, explicitly preserving absolute character index boundaries (`start_char`, `end_char`) for exact frontend DOM coordinate styling and highlighting.
* 📊 **Document Analytics & Readability Engine**: Automatically computes comprehensive linguistic stats—including **Word Count**, **Character Count**, **Average Sentence Length**, **Average Word Length**, **Flesch Reading Ease Score (0-100)**, **Grade-Level Complexity Tier**, and **Estimated Reading Time**.
* 🤖 **Local Generative AI Rewriter**: Integrates with local native `Ollama` models (`llama3`, `qwen2.5:3b`, or `lemma-model`) to paraphrase flagged sentences into **Academic**, **Standard**, or **Creative** tones directly on your device with zero cloud API latency or data leaks.
* 🎨 **Interactive 3D Visual Shell**: Includes a visually stunning dark-mode landing page featuring an interactive **3D Fibonacci Particle Sphere Canvas** that rotates, reacts dynamically to cursor dragging, and gracefully reforms.
* ⚡ **Flexible Async Architecture**: Supports both a zero-dependency **Eager Mode** (synchronous single-process processing) and a full **Async Mode** powered by `Celery` + `Redis` worker queues.
* 📄 **WeasyPrint PDF Automation**: Generates publication-ready PDF academic integrity reports complete with color-coded plagiarism highlighting, match breakdown graphs, and source references.

---

## 🛠️ Technology Stack

| Layer | Technology / Tool |
|---|---|
| **Frontend UI** | HTML5, CSS3 (Custom Stark Dark Theme & Glassmorphism), Vanilla JavaScript, Canvas 3D Physics |
| **API Framework** | FastAPI (Python 3.10+), Pydantic v2, Asynchronous Route Handlers |
| **NLP & ML Pipelines** | `spaCy` (en_core_web_sm), `scikit-learn` (TF-IDF), `sentence-transformers` (all-MiniLM-L6-v2), `faiss-cpu` |
| **Task Queue & Cache** | Celery 5.3+, Redis (with eager mode fallback), SQLite / PostgreSQL metadata |
| **PDF Generation** | WeasyPrint engine |
| **Local LLM Runtime** | Ollama Engine (`lemma-model` custom Qwen2.5 / Llama3 prompt pipeline) |

---

## 📂 Repository Directory Structure

```
lemma-clone/
├── .gitignore                   # Excludes binaries, venv, caches, and build outputs
├── Modelfile                    # Optimized Ollama model configuration file
├── README.md                    # Platform documentation
├── pytest.ini                   # Pytest suite configuration
├── requirements.txt             # Root dependencies manifest
├── run.bat                      # Windows setup and development runner
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py            # Platform environment configuration
│   │   ├── main.py              # FastAPI endpoints & static file hosting
│   │   ├── data/
│   │   │   └── mock_references.json  # Reference corpus text database
│   │   ├── schemas/
│   │   │   ├── document.py      # Pydantic models for upload & metrics
│   │   │   └── rewrite.py       # Pydantic models for text paraphrasing
│   │   ├── services/
│   │   │   ├── analytics.py     # Readability & document metric calculator
│   │   │   ├── database.py      # SQLite / PostgreSQL interaction layer
│   │   │   ├── elasticsearch_client.py # Search index client
│   │   │   ├── extractor.py     # PDF, DOCX, TXT document parser
│   │   │   ├── llm.py           # Local Ollama client & prompt generator
│   │   │   ├── matcher.py       # Lexical (TF-IDF) & Semantic (FAISS) matcher
│   │   │   ├── online_retriever.py  # Ephemeral candidate web retriever
│   │   │   ├── pdf_generator.py # WeasyPrint PDF report renderer
│   │   │   └── segmenter.py     # spaCy coordinate-preserving sentence segmenter
│   │   └── tasks/
│   │       ├── celery_app.py    # Celery queue initialization
│   │       └── analysis.py      # Background document processing worker
│   └── tests/                   # Pytest test suite
│       ├── test_analytics.py    # Unit tests for analytics service
│       ├── test_async_queue.py  # Async upload & job polling tests
│       ├── test_extractor.py    # Document extractor tests
│       ├── test_main.py         # API endpoint integration tests
│       ├── test_matcher.py      # Matcher dual-engine tests
│       ├── test_pdf.py          # PDF generation tests
│       ├── test_rewrite.py      # LLM rewriter tests
│       └── test_segmenter.py    # Sentence segmenter tests
└── frontend/                    # Modern Dark-Theme Frontend
    ├── index.html               # Landing page with 3D Fibonacci Particle Sphere
    ├── dashboard.html           # Document viewer, plagiarism report, & paraphraser
    ├── config.json              # Client API connection config
    └── assets/                  # Frontend JavaScript modules & stylesheet
        ├── css/
        │   └── style.css        # Custom CSS design system
        └── js/
            ├── app.js           # Dashboard controller & document renderer
            └── landing.js       # 3D canvas physics animation loop
```

---

## ⚙️ Quick Start (Local Setup)

### Prerequisites

* **Python**: `3.10` or higher (tested up to `3.14`).
* **Ollama**: Installed locally from [ollama.com](https://ollama.com).

### 1. Configure Local Ollama Model
To run AI paraphrasing locally without memory errors, build the custom model:
```powershell
# 1. Pull base model
ollama pull llama3

# 2. Create optimized Lemma model
ollama create lemma-model -f Modelfile

# 3. Test running the model
ollama run lemma-model
```

### 2. Launch Development Environment (Windows)
Run the root automated startup script:
```powershell
.\run.bat
```
This script will:
1. Create a Python virtual environment (`venv`) if needed.
2. Install all backend dependencies from `backend/requirements.txt`.
3. Download the `spacy` English language model (`en_core_web_sm`).
4. Start the FastAPI development server at `http://localhost:8000`.

---

## 📡 API Endpoint Reference

### System & Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` or `/api/v1/health` | Service health status (DB, Elasticsearch, Ollama, Celery) |
| `GET` | `/api/info` or `/api/v1/system/info` | Platform engine specifications, capabilities, and settings |

### Document Upload & Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/documents/upload` | Synchronously upload, extract text, segment sentences, and calculate readability metrics |
| `POST` | `/api/analyze` or `/api/v1/analyze` | Asynchronously upload file (`.txt`, `.docx`, `.pdf`), start background analysis job, and return `job_id` |
| `GET` | `/api/status/{job_id}` or `/api/v1/status/{job_id}` | Poll background job status and retrieve full analysis & metrics result payload |

### Rewriting & Export

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/rewrite` or `/api/v1/rewrite` | Paraphrase sentence/paragraph using local Ollama model (`tone`: `academic`, `standard`, `creative`) |
| `GET` | `/api/report/{job_id}` or `/api/v1/documents/report/{job_id}` | Download publication-ready PDF integrity report for completed job |

---

## 🧪 Running the Test Suite

Run the full pytest suite with Python path configured:

```powershell
$env:PYTHONPATH="backend"
python -m pytest backend/tests/
```

---

## 🗺️ Roadmap & Phase Status

* [x] **Phase 1**: Ingestion, Parsing & spaCy Coordinate Sentence Segmenter
* [x] **Phase 2**: Dual-Tier Lexical (TF-IDF) & Semantic (FAISS / Vector) Plagiarism Matcher
* [x] **Phase 3**: Celery Asynchronous Processing & Ollama Generative Rewriter Workspace
* [x] **Phase 4**: Document Analytics Engine (Flesch Readability, Word Count, Reading Time)
* [x] **Phase 5**: Dark-Theme Dashboard UI with 3D Fibonacci Canvas & Real-Time Metrics
* [x] **Phase 6**: WeasyPrint PDF Export & End-to-End Automated Testing

---

## 📄 License
This project is open-source under the MIT License.
