# Lemma 🎓

> **Local-First Plagiarism Detection, Document Intelligence & AI Rewriting Platform**

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Netlify](https://img.shields.io/badge/Netlify-Ready-00C7B7?style=flat-square&logo=netlify)](https://netlify.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Lemma](https://img.shields.io/badge/Lemma-2.0-blueviolet?style=flat-square)](https://github.com/Devengoyal885/lemma-clone)

Lemma is a high-performance, **privacy-first** plagiarism detection engine that works completely locally on your machine. No cloud uploads. No API keys. No subscriptions. Analyze documents for plagiarism, receive detailed originality reports, get AI rewriting suggestions—all without leaving your device.

Perfect for:
- ✍️ Students writing essays and thesis papers
- 🏫 Educators checking student submissions
- 🔬 Researchers ensuring original contributions
- 💼 Content creators verifying text authenticity
- ⚖️ Legal professionals confirming document originality


---

## ✨ Key Features

### 🔍 Dual-Tier Plagiarism Detection
- **Lexical Matching**: TF-IDF + Cosine Similarity for exact/near-exact copy detection
- **Semantic Matching**: SentenceTransformer embeddings for paraphrased content detection
- **Hybrid Scoring**: Combined confidence scores for accuracy
- **Character-Level Precision**: Exact coordinate mapping (`start_char`, `end_char`) for highlighting

### 📊 Rich Document Analytics
- Word count, character count, sentence count
- Flesch Reading Ease score (0-100)
- Grade-level complexity assessment
- Estimated reading time
- Lexical diversity metrics

### 🤖 AI-Powered Text Rewriting
- Local LLM support via **Ollama** (no cloud calls)
- Multiple tone options: Academic, Professional, Standard, Creative
- Graceful fallback when Ollama unavailable
- Preserves meaning while eliminating plagiarism

### 📄 Professional PDF Reports
- Publication-ready PDF generation
- Color-coded plagiarism highlighting
- Detailed match breakdown
- Source attribution
- Statistical summaries

### 🌐 Web-Based UI
- Dark/Light theme toggle
- Responsive design (mobile, tablet, desktop)
- Real-time progress indicators
- Analysis history with localStorage
- Drag-and-drop file upload

### ⚡ Two Execution Modes

#### **Lite Mode** (Default - No Dependencies)
- Works **without** PostgreSQL, Elasticsearch, Redis, Docker
- Uses local JSON reference corpus
- TF-IDF + optional SentenceTransformer
- Perfect for local development and deployment
- Instant startup, minimal resource usage

#### **Advanced Mode** (Optional - Full Infrastructure)
- PostgreSQL + pgvector for vector search
- Elasticsearch for full-text search
- Redis + Celery for async job processing
- Online retrieval (Semantic Scholar API)
- FAISS indexing for faster similarity search

Automatic fallback: If PostgreSQL is unavailable, Lemma switches to Lite Mode seamlessly.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Canvas |
| **Backend API** | FastAPI (Python 3.10+), Pydantic v2 |
| **NLP/ML** | spaCy, scikit-learn (TF-IDF), SentenceTransformers |
| **Document Processing** | pypdf, python-docx, PyPDF2 |
| **PDF Generation** | WeasyPrint |
| **Local LLM** | Ollama (llama3, qwen2.5, custom models) |
| **Optional Infrastructure** | PostgreSQL + pgvector, Elasticsearch, Redis, Celery |
| **Deployment** | Netlify (frontend), Heroku/Railway/Fly.io (backend) |
| **Testing** | pytest |

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- **Python 3.10+** ([download](https://python.org/downloads))
- **Git** ([download](https://git-scm.com))
- ✅ No Docker required
- ✅ No PostgreSQL required
- ✅ No API keys required

### Step 1: Clone Repository

```bash
git clone https://github.com/Devengoyal885/lemma-clone.git
cd lemma-clone
```

### Step 2: Run Setup & Start Server

**Windows:**
```bash
run.bat
```

**macOS/Linux:**
```bash
chmod +x run.sh
./run.sh
```

The script will:
1. ✅ Create Python virtual environment
2. ✅ Install dependencies
3. ✅ Download spaCy English model
4. ✅ Start FastAPI server on port 8000

### Step 3: Open in Browser

```
http://localhost:8000
```

Done! 🎉 You now have a fully functional plagiarism detection engine running locally.

---

## 📖 Usage Guide

### Upload & Analyze
1. Click **"Upload Document"** or **"Paste Text"**
2. Select PDF, DOCX, or TXT file (or paste text directly)
3. Click **"Analyze"**
4. View plagiarism score, originality score, and flagged passages
5. Click highlighted sections to see source references

### Rewrite Flagged Text
1. Select a plagiarism match in the results
2. Click **"Rewrite"** (requires Ollama running)
3. Choose tone: Academic, Professional, Standard, or Creative
4. Compare original vs. rewritten text
5. Click **"Replace in Document"** to update text
6. Re-analyze to see improved originality score

### Generate Report
1. After analysis completes, click **"Download Report"**
2. Receive a professional PDF with:
   - Plagiarism percentage
   - Originality score
   - All flagged passages
   - Source references
   - Document statistics

### View Analysis History
1. Go to **"History"** tab
2. See all previous analyses with scores
3. Click **"View"** to reload analysis
4. Click **"Delete"** to remove from history

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Lite Mode (default - no external services)
LEMMA_MODE=lite
LEMMA_CELERY_ALWAYS_EAGER=true

# File uploads
LEMMA_MAX_FILE_SIZE_MB=100
LEMMA_ALLOWED_EXTENSIONS=pdf,docx,txt

# NLP models
LEMMA_SPACY_MODEL=en_core_web_sm
LEMMA_SENTENCE_TRANSFORMERS_MODEL=all-MiniLM-L6-v2

# Plagiarism thresholds (0.0-1.0)
LEMMA_LEXICAL_THRESHOLD=0.70
LEMMA_SEMANTIC_THRESHOLD=0.65
LEMMA_HYBRID_THRESHOLD=0.60

# Optional: Ollama for text rewriting
LEMMA_OLLAMA_URL=http://127.0.0.1:11434
LEMMA_OLLAMA_MODEL=lemma-model

# Optional: PostgreSQL (Advanced Mode)
LEMMA_DATABASE_URL=
LEMMA_POSTGRES_HOST=localhost
LEMMA_POSTGRES_PORT=5432

# Optional: Elasticsearch (Advanced Mode)
LEMMA_ELASTICSEARCH_URL=http://localhost:9200

# Optional: Redis & Celery
LEMMA_REDIS_URL=redis://localhost:6379/0
```

---

## 🐳 Advanced Setup (With PostgreSQL & Elasticsearch)

For the full experience with vector search and async processing:

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM available
- 2GB disk space

### Run with Docker

```bash
docker-compose up -d
```

This starts:
- FastAPI backend on `http://localhost:8000`
- PostgreSQL 15 on `localhost:5432`
- Elasticsearch 8 on `localhost:9200`
- Redis on `localhost:6379`

### Create Database Schema

```bash
docker-compose exec backend python -m backend.scripts.init_db
```

---

## 🦙 Ollama Setup (AI Text Rewriting)

### Install Ollama

1. Download from [ollama.com](https://ollama.com)
2. Install and start the Ollama service

### Pull & Customize a Model

```bash
# Option 1: Use existing model
ollama pull qwen2.5:3b

# Option 2: Create custom Lemma model (optimized)
ollama create lemma-model -f Modelfile
```

### Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

Should return a list of available models. If Ollama is offline, Lemma gracefully disables the rewrite feature.

---

## 🌐 Netlify Deployment (Frontend)

### Prerequisites
- Frontend files in `frontend/` folder
- GitHub repository
- Netlify account (free)

### Step 1: Connect Repository to Netlify

1. Go to [netlify.com](https://netlify.com)
2. Click **"New site from Git"**
3. Authorize GitHub and select your Lemma repository
4. Set publish directory to **`frontend`**
5. No build command needed (static files)

### Step 2: Configure Environment Variables

In Netlify dashboard, go to **Site Settings → Build & Deploy → Environment**:

```
BACKEND_API_URL=https://your-backend-domain.com
ENVIRONMENT=production
THEME_MODE=dark
```

### Step 3: Configure SPA Routing

The repository includes `netlify.toml` and `frontend/_redirects` which Netlify will auto-detect.

### Deploy Backend

Choose one of:

**Option A: Heroku** (free tier no longer available, but still works with credit)
```bash
heroku login
heroku create lemma-backend
git push heroku main
```

**Option B: Railway.app** (recommended for free tier)
1. Connect GitHub repository
2. Auto-detect Python/FastAPI
3. Set environment variables in dashboard
4. Deploy

**Option C: Fly.io**
```bash
flyctl launch
flyctl deploy
```

### Update Frontend Configuration

After deploying backend, update `frontend/config.json`:

```json
{
  "BACKEND_API_URL": "https://your-backend-url.herokuapp.com",
  "ENVIRONMENT": "production"
}
```

Push changes and Netlify auto-deploys.

---

## 📡 API Reference

### Health & System Status

#### `GET /health`
Returns service health status and available features.

**Response (200):**
```json
{
  "status": "ok",
  "mode": "lite",
  "services": {
    "postgres": false,
    "elasticsearch": false,
    "redis": false,
    "ollama": false
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /api/v1/system/info`
Returns platform capabilities and model information.

**Response (200):**
```json
{
  "version": "2.0.0",
  "mode": "lite",
  "capabilities": {
    "text_analysis": true,
    "pdf_upload": true,
    "rewriting": false,
    "async_processing": false
  },
  "models": {
    "spacy": "en_core_web_sm",
    "sentence_transformers": "all-MiniLM-L6-v2"
  }
}
```

### Text Analysis (Lite Mode)

#### `POST /api/v1/analyze/text`
Analyze plain text for plagiarism without file upload.

**Request:**
```json
{
  "text": "Your document text here...",
  "title": "Essay Title (optional)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "title": "Essay Title",
  "plagiarism_score": 23,
  "originality_score": 77,
  "total_sentences": 15,
  "matched_sentences_count": 3,
  "metrics": {
    "word_count": 342,
    "character_count": 1852,
    "reading_ease": 65,
    "grade_level": "10th grade",
    "reading_time_minutes": 2
  },
  "matches": [
    {
      "query_text": "The quick brown fox",
      "matched_text": "The quick brown fox",
      "score": 0.98,
      "match_type": "lexical",
      "doc_title": "Reference Document",
      "doc_author": "Unknown",
      "sentence_index": 2
    }
  ],
  "mode": "lite"
}
```

### Document Upload & Analysis

#### `POST /api/v1/documents/upload`
Upload and synchronously analyze a document.

**Request:**
```
Content-Type: multipart/form-data
file: [PDF/DOCX/TXT file]
```

**Response (200):**
```json
{
  "status": "success",
  "document_id": "doc_123456",
  "filename": "essay.pdf",
  "text_length": 5420,
  "plagiarism_score": 18,
  "originality_score": 82,
  "matches": [...]
}
```

### Text Rewriting

#### `POST /api/v1/rewrite`
Rewrite text using local Ollama model.

**Request:**
```json
{
  "text": "Text to rewrite...",
  "tone": "academic"
}
```

**Response (200):**
```json
{
  "status": "success",
  "original": "Text to rewrite...",
  "rewritten": "Revised text using academic tone...",
  "tone": "academic"
}
```

**Error Response (503):**
```json
{
  "status": "error",
  "error": "Ollama service unavailable",
  "message": "Rewriting disabled. Start Ollama to enable this feature."
}
```

---

## 🧪 Testing

### Run All Tests

```bash
# Set Python path
export PYTHONPATH=backend  # macOS/Linux
set PYTHONPATH=backend     # Windows

# Run pytest
python -m pytest backend/tests/ -v
```

### Run Specific Test Suite

```bash
# Lite Mode tests (no dependencies)
python -m pytest backend/tests/test_matcher.py -v

# Analytics tests
python -m pytest backend/tests/test_analytics.py -v

# Text extraction tests
python -m pytest backend/tests/test_extractor.py -v
```

### Test Coverage

```bash
python -m pytest backend/tests/ --cov=backend/app --cov-report=html
```

---

## 📁 Project Structure

```
lemma-clone/
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── pytest.ini                       # Test configuration
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── run.bat                          # Windows startup script
├── run.sh                           # macOS/Linux startup script
├── Modelfile                        # Ollama model configuration
├── docker-compose.yml               # Docker infrastructure
├── netlify.toml                     # Netlify deployment config
│
├── backend/                         # FastAPI Backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app + all endpoints
│   │   ├── config.py                # Configuration management
│   │   ├── data/
│   │   │   └── mock_references.json # Reference corpus (Lite Mode)
│   │   ├── schemas/
│   │   │   ├── document.py          # Document Pydantic models
│   │   │   └── rewrite.py           # Rewrite request/response models
│   │   ├── services/
│   │   │   ├── analytics.py         # Document metrics calculator
│   │   │   ├── database.py          # PostgreSQL client
│   │   │   ├── elasticsearch_client.py # Elasticsearch client
│   │   │   ├── extractor.py         # PDF/DOCX/TXT parser
│   │   │   ├── llm.py               # Ollama wrapper
│   │   │   ├── lite_matcher.py      # TF-IDF plagiarism engine
│   │   │   ├── matcher.py           # Advanced dual-tier matcher
│   │   │   ├── matcher_factory.py   # Auto-detection factory
│   │   │   ├── pdf_generator.py     # PDF report generation
│   │   │   ├── segmenter.py         # Sentence segmentation
│   │   │   └── online_retriever.py  # Web-based candidate retriever
│   │   └── tasks/
│   │       ├── celery_app.py        # Celery queue config
│   │       └── analysis.py          # Background task workers
│   ├── tests/                       # Pytest test suite
│   │   ├── test_analytics.py
│   │   ├── test_extractor.py
│   │   ├── test_matcher.py
│   │   ├── test_pdf.py
│   │   ├── test_rewrite.py
│   │   └── ...
│   └── scripts/
│       └── backfill_elasticsearch.py # Index population script
│
└── frontend/                        # React-Free Static UI
    ├── index.html                   # Landing page
    ├── dashboard.html               # Main application
    ├── config.json                  # Runtime configuration
    ├── _redirects                   # Netlify SPA routing
    └── assets/
        ├── css/
        │   ├── style.css            # Main stylesheet
        │   └── mobile.css           # Mobile responsive styles
        └── js/
            ├── app.js               # Dashboard logic
            ├── config.js            # API config manager
            ├── landing.js           # 3D particle animation
            └── mobile-ui.js         # Mobile enhancements
```

---

## ⚖️ Lite Mode vs. Advanced Mode

| Feature | Lite Mode | Advanced Mode |
|---|---|---|
| **Setup Time** | < 1 minute | 5-10 minutes |
| **External Dependencies** | None | PostgreSQL, Elasticsearch, Redis |
| **Reference Corpus** | Local JSON | PostgreSQL (scalable) |
| **Matching Speed** | ~100-500ms | ~50-200ms (cached) |
| **Maximum Documents** | ~1,000 references | 1M+ references |
| **Async Processing** | Synchronous | Celery + Redis |
| **Scalability** | Single machine | Distributed cluster |
| **Cost** | Free | Infrastructure costs |
| **Perfect For** | Students, small teams, local dev | Enterprises, production SaaS |

---

## 🔒 Privacy & Security

### No Cloud Uploads
- All processing happens on your machine
- Documents never leave your device
- No telemetry or analytics tracking

### No API Keys Required
- No dependency on external services
- No subscription fees
- No vendor lock-in

### Data Safety
- Optional PostgreSQL encryption for Advanced Mode
- Temporary files auto-deleted after analysis
- SSL/TLS support for Netlify deployment

### Open Source
- Full source code available
- Audit-friendly codebase
- MIT License

---

## 🐛 Troubleshooting

### Backend won't start

**Problem:** "Connection refused" when opening http://localhost:8000

**Solution:**
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                # macOS/Linux

# Kill process or use different port
# Then restart with: uvicorn backend.app.main:app --port 8001
```

### Ollama not available

**Problem:** Rewrite button disabled, error "Ollama service unavailable"

**Solution:**
1. Install Ollama from [ollama.com](https://ollama.com)
2. Start Ollama service: `ollama serve`
3. Pull a model: `ollama pull qwen2.5:3b`
4. Refresh browser

Lemma works fine without Ollama—it just disables text rewriting.

### PostgreSQL connection error

**Problem:** Advanced Mode features not working

**Solution:**
1. Ensure PostgreSQL is running
2. Check `.env` for correct `LEMMA_DATABASE_URL`
3. Run: `python -m backend.scripts.init_db`
4. Restart backend: `python -m uvicorn backend.app.main:app`

If PostgreSQL unavailable, Lemma automatically falls back to Lite Mode.

### PDF generation fails

**Problem:** "Error generating PDF" when clicking download

**Solution:**
1. Ensure WeasyPrint dependencies installed: `pip install -r requirements.txt`
2. Check file permissions in `backend/` directory
3. Verify 500MB+ free disk space

On Linux, may need: `sudo apt-get install libssl-dev libffi-dev python3-dev`

### File upload fails

**Problem:** "File type not supported" or upload timeout

**Solution:**
- Maximum file size: 100MB (configurable via `.env`)
- Supported formats: PDF, DOCX, TXT
- For large files (>50MB), use Lite Mode text analysis instead

---

## 📊 Performance Benchmarks

Tested on M1 MacBook Pro with 16GB RAM:

| Operation | Lite Mode | Advanced Mode |
|---|---|---|
| Text analysis (500 words) | ~150ms | ~80ms |
| PDF parsing (5MB) | ~300ms | ~300ms |
| Plagiarism matching | ~200ms | ~50ms |
| PDF report generation | ~500ms | ~500ms |
| **Total (upload → report)** | **~1.2s** | **~0.9s** |

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and write tests
4. Run tests: `python -m pytest backend/tests/ -v`
5. Commit: `git commit -m "feat: description"`
6. Push and create Pull Request

### Code Style
- Python: PEP 8 via Black formatter
- JavaScript: Standard ES6+
- Commit messages: Conventional Commits

---

## 📄 License

Licensed under the **MIT License**. See [LICENSE](LICENSE) file for details.

Free for personal, educational, and commercial use.

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework
- [spaCy](https://spacy.io) - Industrial-strength NLP
- [scikit-learn](https://scikit-learn.org) - Machine learning library
- [Ollama](https://ollama.ai) - Local LLM runtime
- [WeasyPrint](https://weasyprint.org) - HTML to PDF
- [SentenceTransformers](https://www.sbert.net) - Semantic embeddings
- [PostgreSQL](https://postgresql.org) + [Elasticsearch](https://elastic.co) - Optional infrastructure

---

## 💡 Educational Value

Lemma is ideal for:
- **Computer Science students** learning NLP, information retrieval, and plagiarism detection algorithms
- **Machine Learning practitioners** experimenting with TF-IDF, embeddings, and hybrid ranking
- **Full-stack developers** building production applications with FastAPI, vector databases, and async processing
- **Educators** teaching academic integrity through hands-on plagiarism detection tools

---

## 🗺️ Roadmap

### **v2.1** (Q2 2024)
- [ ] GitHub Actions CI/CD workflow
- [ ] Docker multi-stage builds for production
- [ ] Caching layer for repeated analyses
- [ ] Bulk upload/batch analysis API

### **v2.2** (Q3 2024)
- [ ] Custom reference corpus upload
- [ ] Advanced filtering (by author, date range, source)
- [ ] Detailed source attribution and citation formatting
- [ ] Export to multiple formats (JSON, XML, CSV)

### **v3.0** (Q4 2024)
- [ ] GPT-4 integration for AI rewriting (cloud optional)
- [ ] Paraphrase detection with structural analysis
- [ ] API rate limiting and authentication
- [ ] Multi-language support
- [ ] Real-time collaboration features

---

## 📬 Support & Feedback

- **Issues**: [GitHub Issues](https://github.com/Devengoyal885/lemma-clone/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Devengoyal885/lemma-clone/discussions)
- **Email**: devengoyal885@gmail.com

---

<div align="center">

**Made with ❤️ for students, educators, and researchers**

[⭐ Star on GitHub](https://github.com/Devengoyal885/lemma-clone) | [🐛 Report Issue](https://github.com/Devengoyal885/lemma-clone/issues) | [💬 Discuss](https://github.com/Devengoyal885/lemma-clone/discussions)

</div>
