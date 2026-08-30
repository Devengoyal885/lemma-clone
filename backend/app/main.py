import uuid
# pyrefly: ignore [missing-import]
from celery.result import AsyncResult
# pyrefly: ignore [missing-import]
import os
from sqlalchemy import create_engine
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.config import settings
from app.services.pdf_generator import PDFGeneratorService
from app.schemas.document import DocumentUploadResponse, SentenceCoordinate
from app.schemas.rewrite import RewriteRequest, RewriteResponse
from app.services.extractor import (
    DocumentExtractorService,
    FileSizeExceededError,
    UnsupportedFileTypeError,
    ExtractionError,
)
from app.services.segmenter import SentenceSegmenterService
from app.services.matcher import DualTierMatcher
from app.services.llm import LLMService
from app.services.analytics import DocumentAnalyticsService
from app.tasks.celery_app import celery_app
from app.tasks.analysis import analyze_document_task

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
   DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/lemma"

engine = create_engine(DATABASE_URL)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Plagiarism Detection and Text Rewriting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, we would restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(FileSizeExceededError)
async def file_size_exceeded_handler(request, exc: FileSizeExceededError):
    return JSONResponse(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        content={"detail": str(exc)},
    )

@app.exception_handler(UnsupportedFileTypeError)
async def unsupported_file_type_handler(request, exc: UnsupportedFileTypeError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )

@app.exception_handler(ExtractionError)
async def extraction_error_handler(request, exc: ExtractionError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    # Log this in a production app
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )

from pathlib import Path
from fastapi.staticfiles import StaticFiles

@app.get("/health")
@app.get(f"{settings.API_V1_STR}/health")
async def health():
    import logging
    import asyncio
    import httpx
    import anyio
    import socket
    from urllib.parse import urlparse
    from app.services.database import DatabaseService
    
    local_logger = logging.getLogger("health_check")
    
    # Clean loopback helper to prevent Windows getaddrinfo latency
    def clean_host(host_str: str) -> str:
        if host_str and host_str.lower() == "localhost":
            return "127.0.0.1"
        return host_str

    # Socket precheck helper
    def is_port_open_sync(h: str, p: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                return s.connect_ex((clean_host(h), p)) == 0
        except Exception:
            return False

    async def is_port_open(h: str, p: int) -> bool:
        return await anyio.to_thread.run_sync(is_port_open_sync, h, p)

    # Parse Postgres host/ports
    db_host = settings.POSTGRES_HOST
    db_port = int(settings.POSTGRES_PORT or 5432)
    db_url = settings.DATABASE_URL
    if db_url:
        try:
            parsed = urlparse(db_url)
            if parsed.hostname:
                db_host = parsed.hostname
            if parsed.port:
                db_port = parsed.port
        except Exception:
            pass

    # Parse Redis host/ports
    redis_host = "localhost"
    redis_port = 6379
    redis_url = settings.REDIS_URL
    if redis_url:
        try:
            parsed = urlparse(redis_url)
            if parsed.hostname:
                redis_host = parsed.hostname
            if parsed.port:
                redis_port = parsed.port
        except Exception:
            pass

    # 1. Define PostgreSQL checker task
    async def check_database():
        if not await is_port_open(db_host, db_port):
            return "disconnected"
        try:
            def check_db():
                conn = DatabaseService.get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1;")
                conn.close()
                return "connected"
                
            return await asyncio.wait_for(
                anyio.to_thread.run_sync(check_db),
                timeout=1.0
            )
        except Exception as e:
            local_logger.warning(f"Health check: Database connection failed: {e}")
            return "disconnected"

    # 2. Define Elasticsearch checker task
    async def check_elasticsearch():
        try:
            async with httpx.AsyncClient(timeout=0.8) as client:
                res = await client.get(settings.ELASTICSEARCH_URL)
                if res.status_code == 200:
                    return "healthy"
                else:
                    return "unhealthy"
        except Exception as e:
            local_logger.warning(f"Health check: Elasticsearch ping failed: {e}")
            return "offline"

    # 3. Define Ollama checker task
    async def check_ollama():
        try:
            # Check Ollama status directly with a fast 1.0s timeout
            url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    status_val = "running" if models else "no_models"
                    return status_val, models
                else:
                    return "offline", []
        except Exception as e:
            local_logger.warning(f"Health check: Ollama check failed: {e}")
            return "offline", []

    # 4. Define Celery checker task
    async def check_celery_status():
        if settings.CELERY_ALWAYS_EAGER:
            return "idle"
            
        if not await is_port_open(redis_host, redis_port):
            return "offline"
            
        try:
            def check_celery():
                inspector = celery_app.control.inspect(timeout=0.5)
                active_tasks = inspector.active()
                if active_tasks:
                    has_active = any(len(tasks) > 0 for tasks in active_tasks.values() if tasks)
                    if has_active:
                        return "working"
                return "idle"
                
            return await asyncio.wait_for(
                anyio.to_thread.run_sync(check_celery),
                timeout=1.0
            )
        except Exception as e:
            local_logger.warning(f"Health check: Celery status check failed: {e}")
            return "offline"

    # Run all checks in parallel
    db_task = check_database()
    es_task = check_elasticsearch()
    ollama_task = check_ollama()
    celery_task = check_celery_status()
    
    db_status, es_status, (ollama_status, available_models), celery_status = await asyncio.gather(
        db_task, es_task, ollama_task, celery_task
    )

    # Determine general status
    general_status = "ok"
    if db_status == "disconnected" or es_status == "offline" or ollama_status == "offline":
        general_status = "degraded"

    return {
        "status": general_status,
        "project": settings.PROJECT_NAME,
        "services": {
            "database": {
                "status": db_status
            },
            "elasticsearch": {
                "status": es_status
            },
            "ollama": {
                "status": ollama_status,
                "model": settings.OLLAMA_MODEL,
                "available_models": available_models
            },
            "celery": {
                "status": celery_status
            }
        }
    }


@app.get(
    f"{settings.API_V1_STR}/system/info",
    status_code=status.HTTP_200_OK,
    summary="Get engine specifications and capabilities",
    description="Returns platform capability details, allowed formats, tone options, and active algorithms."
)
@app.get("/api/info", include_in_schema=False)
async def get_system_info():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.1.0",
        "description": "Local-first Plagiarism Detection and Generative Academic Rewriting Platform",
        "capabilities": {
            "supported_formats": [f".{ext}" for ext in settings.ALLOWED_EXTENSIONS],
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "spacy_model": settings.SPACY_MODEL,
            "ollama_model": settings.OLLAMA_MODEL,
            "rewriting_tones": ["academic", "standard", "creative"],
            "execution_mode": "Eager (Sync)" if settings.CELERY_ALWAYS_EAGER else "Celery + Redis Queue",
            "features": [
                "Lexical TF-IDF Cosine Similarity Engine",
                "Semantic Vector Indexing (Sentence-Transformers + FAISS / HNSW)",
                "Preserved Absolute Coordinate Mapping (start_char, end_char)",
                "Readability Analytics & Flesch Metric Calculation Engine",
                "Local Generative AI Tone Paraphraser",
                "Publication-Ready WeasyPrint PDF Exporter"
            ]
        }
    }


# Global/lazy instance of the plagiarism matching engine
# Uses MatcherFactory to automatically select Lite or Advanced mode
matcher_instance = None

def get_matcher():
    global matcher_instance
    if matcher_instance is None:
        from app.services.matcher_factory import MatcherFactory
        matcher_instance = MatcherFactory.initialize()
    return matcher_instance

def get_matcher_mode():
    """Get the current matcher mode (lite or advanced)"""
    from app.services.matcher_factory import MatcherFactory
    return MatcherFactory.get_mode()

async def check_service_port_open(host_str: str, port_val: int) -> bool:
    import socket
    import anyio
    def check_sync():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                target = "127.0.0.1" if host_str.lower() == "localhost" else host_str
                return s.connect_ex((target, port_val)) == 0
        except Exception:
            return False
    return await anyio.to_thread.run_sync(check_sync)

async def check_postgres_available() -> bool:
    """Check if PostgreSQL is available (returns True/False, doesn't throw)"""
    from urllib.parse import urlparse
    db_host = settings.POSTGRES_HOST
    db_port = int(settings.POSTGRES_PORT or 5432)
    db_url = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
    if db_url:
        try:
            parsed = urlparse(db_url)
            if parsed.hostname: db_host = parsed.hostname
            if parsed.port: db_port = parsed.port
        except Exception:
            pass
    return await check_service_port_open(db_host, db_port)

async def check_elasticsearch_available() -> bool:
    """Check if Elasticsearch is available (returns True/False, doesn't throw)"""
    from urllib.parse import urlparse
    es_host = "localhost"
    es_port = 9200
    if settings.ELASTICSEARCH_URL:
        try:
            parsed = urlparse(settings.ELASTICSEARCH_URL)
            if parsed.hostname: es_host = parsed.hostname
            if parsed.port: es_port = parsed.port
        except Exception:
            pass
    return await check_service_port_open(es_host, es_port)

async def check_ollama_online():
    from urllib.parse import urlparse
    ollama_host = "127.0.0.1"
    ollama_port = 11434
    if settings.OLLAMA_URL:
        try:
            parsed = urlparse(settings.OLLAMA_URL)
            if parsed.hostname: ollama_host = parsed.hostname
            if parsed.port: ollama_port = parsed.port
        except Exception:
            pass
    if not await check_service_port_open(ollama_host, ollama_port):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama service is offline. Please make sure Ollama is running locally on your system."
        )


# Text Analysis Request/Response Models
from pydantic import BaseModel

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to analyze")
    title: str = Field(default="Pasted Text", description="Optional document title")

class TextAnalysisResponse(BaseModel):
    status: str = Field(..., description="Analysis status")
    plagiarism_score: float = Field(..., description="Plagiarism percentage (0-100)")
    originality_score: float = Field(..., description="Originality percentage (0-100)")
    total_sentences: int = Field(..., description="Total sentences analyzed")
    matched_sentences_count: int = Field(..., description="Number of plagiarized sentences")
    metrics: dict = Field(..., description="Document analytics")
    matches: list = Field(default_factory=list, description="Plagiarism matches")
    mode: str = Field(..., description="Analysis mode (lite or advanced)")


@app.post(
    f"{settings.API_V1_STR}/analyze/text",
    response_model=TextAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze pasted text for plagiarism",
    description="Analyzes raw text input for plagiarism without file upload. Works in Lite Mode without external dependencies."
)
async def analyze_text_direct(payload: TextAnalysisRequest):
    """
    Direct text plagiarism analysis endpoint.
    Works with Lite Mode (local TF-IDF matching) by default.
    Falls back gracefully if external services are unavailable.
    """
    import json
    from app.services.segmenter import SentenceSegmenterService
    from app.services.analytics import DocumentAnalyticsService
    from app.services.lite_matcher import LiteMatcher
    
    # Validate input
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty"
        )
    
    text = payload.text.strip()
    
    # Get current matcher (automatically selects Lite or Advanced mode)
    matcher_mode = get_matcher_mode()
    matcher = get_matcher()
    
    # Segment sentences
    sentences_data = SentenceSegmenterService.segment(text)
    if not sentences_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not segment text into sentences. Ensure text is not too short."
        )
    
    # Calculate analytics
    metrics_data = DocumentAnalyticsService.analyze_readability(text, len(sentences_data))
    
    # Perform plagiarism analysis
    all_matches = []
    matched_sentence_count = 0
    matched_word_count = 0
    total_word_count = metrics_data.get("word_count", 0)
    
    try:
        # Use Lite Matcher for text analysis (more direct approach)
        lite_matcher = LiteMatcher()
        
        for sent_idx, sent_data in enumerate(sentences_data):
            sent_text = sent_data["text"]
            sent_start = sent_data["start_char"]
            sent_end = sent_data["end_char"]
            
            # Find hybrid matches
            matches = lite_matcher.find_hybrid_matches(sent_text, top_k=3)
            
            if matches:
                matched_sentence_count += 1
                # Get matching phrases
                if matches:
                    best_match = matches[0]
                    phrases = lite_matcher.extract_matching_phrases(sent_text, best_match.get("matched_text", ""))
                    
                    all_matches.append({
                        "sentence_index": sent_idx,
                        "query_text": sent_text,
                        "query_start": sent_start,
                        "query_end": sent_end,
                        "matched_text": best_match.get("matched_text", ""),
                        "match_type": best_match.get("match_type", "hybrid"),
                        "score": float(best_match.get("hybrid_score", best_match.get("combined_score", 0))),
                        "doc_title": best_match.get("doc_title", "Unknown"),
                        "doc_author": best_match.get("doc_author", "N/A"),
                        "doc_source": best_match.get("doc_source", "N/A"),
                        "phrases": phrases
                    })
                    
                    # Count matched words
                    for phrase in phrases:
                        matched_word_count += len(phrase["text"].split())
    
    except Exception as e:
        import logging
        logging.error(f"Text analysis error: {e}")
        # Gracefully continue with no matches rather than failing
        all_matches = []
        matched_sentence_count = 0
    
    # Calculate plagiarism score
    plagiarism_score = 0.0
    if len(sentences_data) > 0:
        plagiarism_score = (matched_sentence_count / len(sentences_data)) * 100
    
    originality_score = 100.0 - plagiarism_score
    
    return TextAnalysisResponse(
        status="completed",
        plagiarism_score=round(plagiarism_score, 2),
        originality_score=round(originality_score, 2),
        total_sentences=len(sentences_data),
        matched_sentences_count=matched_sentence_count,
        metrics=metrics_data,
        matches=all_matches,
        mode=matcher_mode
    )


@app.post(
    f"{settings.API_V1_STR}/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and segment a document",
    description="Ingests a PDF, DOCX, or TXT file, validates constraints, extracts plain text, and segments it."
)
async def upload_document(file: UploadFile = File(...)):
    # Note: Removed database requirements for Lite Mode support
    # This endpoint now works without PostgreSQL/Elasticsearch

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload request."
        )

    # Read content
    content = await file.read()
    
    # Extract text (validations are performed internally)
    text = DocumentExtractorService.extract_text(file.filename, content)
    
    # Segment sentences with coordinates
    sentences_data = SentenceSegmenterService.segment(text)
    
    # Format response
    sentences = [
        SentenceCoordinate(
            text=s["text"],
            start_char=s["start_char"],
            end_char=s["end_char"]
        )
        for s in sentences_data
    ]
    
    # Compute readability metrics
    metrics_data = DocumentAnalyticsService.analyze_readability(text, len(sentences))
    
    return DocumentUploadResponse(
        filename=file.filename,
        text=text,
        char_count=len(text),
        sentence_count=len(sentences),
        sentences=sentences,
        metrics=metrics_data,
        analysis=None
    )

@app.post(
    f"{settings.API_V1_STR}/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Asynchronously analyze a document for plagiarism",
    description="Saves document to disk and queues background analysis task, returning a job ID immediately."
)
@app.post(
    "/api/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False
)
async def analyze_document_async(file: UploadFile = File(...)):
    # Note: Removed hard database requirements for Lite Mode support
    # Check availability but continue anyway (graceful degradation)
    # postgres_available = await check_postgres_available()
    # es_available = await check_elasticsearch_available()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload request."
        )
        
    # Validate extension using settings before writing to disk
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{file_ext}. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
        
    # Generate UUID and setup paths
    job_id = str(uuid.uuid4())
    temp_filename = f"{job_id}_{file.filename}"
    temp_filepath = settings.UPLOAD_DIR / temp_filename
    
    # Read and save in chunks to check file size limit
    content_size = 0
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    
    try:
        with open(temp_filepath, "wb") as f:
            while chunk := await file.read(8192):
                content_size += len(chunk)
                if content_size > max_bytes:
                    raise FileSizeExceededError(f"File size exceeds limit of {settings.MAX_FILE_SIZE_MB}MB.")
                f.write(chunk)
    except FileSizeExceededError as e:
        if temp_filepath.exists():
            temp_filepath.unlink()
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(e)
        )
    except Exception as e:
        if temp_filepath.exists():
            temp_filepath.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save temporary file: {str(e)}"
        )

    # Trigger celery task with custom task ID matching the job ID
    analyze_document_task.apply_async(
        args=[str(temp_filepath), file.filename],
        task_id=job_id
    )
    
    return {
        "job_id": job_id,
        "status": "pending"
    }


@app.get(
    f"{settings.API_V1_STR}/status/{{job_id}}",
    status_code=status.HTTP_200_OK,
    summary="Get background task status and results",
    description="Check the current execution status of an async document plagiarism analysis task."
)
@app.get(
    "/api/status/{job_id}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def get_job_status(job_id: str):
    res = AsyncResult(job_id, app=celery_app)
    
    if res.state == "SUCCESS":
        return {
            "job_id": job_id,
            "status": "completed",
            "result": res.result
        }
    elif res.state == "FAILURE":
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(res.result)
        }
    elif res.state in ("PENDING", "RECEIVED"):
        return {
            "job_id": job_id,
            "status": "pending"
        }
    else:  # STARTED, RETRY, etc.
        return {
            "job_id": job_id,
            "status": "processing"
        }


@app.get(
    f"{settings.API_V1_STR}/documents/report/{{job_id}}",
    summary="Download PDF report for a job",
    description="Generates and returns the official downloadable PDF plagiarism analysis report for a completed job."
)
@app.get(
    "/api/report/{job_id}",
    include_in_schema=False
)
async def get_job_report_pdf(job_id: str):
    res = AsyncResult(job_id, app=celery_app)
    
    if res.state != "SUCCESS":
        if res.state in ("PENDING", "RECEIVED", "STARTED", "RETRY"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plagiarism analysis is still in progress. Please wait for completion before downloading the report."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plagiarism report not found or task failed."
            )
            
    result = res.result
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plagiarism report details are empty or unavailable."
        )
        
    try:
        pdf_bytes = PDFGeneratorService.generate_report(result)
        
        filename = result.get("filename", "lemma_report.txt")
        pdf_filename = filename.rsplit(".", 1)[0] + "_report.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(e)}"
        )



@app.post(
    f"{settings.API_V1_STR}/rewrite",
    response_model=RewriteResponse,
    status_code=status.HTTP_200_OK,
    summary="Rewrite a text segment to eliminate plagiarism",
    description="Uses a local LLM via Ollama to paraphrase a sentence with a professional academic tone."
)
@app.post(
    "/api/rewrite",
    response_model=RewriteResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def rewrite_text_endpoint(payload: RewriteRequest):
    try:
        await check_ollama_online()
        rewritten = await LLMService.rewrite_text(payload.text, tone=payload.tone)
    except HTTPException:
        rewritten = LLMService.fallback_rewrite_text(payload.text, tone=payload.tone)
    except Exception:
        rewritten = LLMService.fallback_rewrite_text(payload.text, tone=payload.tone)

    return RewriteResponse(
        original_text=payload.text,
        rewritten_text=rewritten
    )


# Serve static frontend files
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
# Ensure the directory exists
try:
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not mount static frontend files directory {FRONTEND_DIR}: {e}")

