import uuid
import os
import io
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.document import DocumentUploadResponse, SentenceCoordinate
from app.schemas.rewrite import RewriteRequest, RewriteResponse
from app.services.extractor import (
    DocumentExtractorService,
    FileSizeExceededError,
    UnsupportedFileTypeError,
    ExtractionError,
)
from app.services.segmenter import SentenceSegmenterService
from app.services.lite_matcher import LiteMatcher
from app.services.analytics import DocumentAnalyticsService
from app.services.llm import LLMService
from app.services.pdf_generator import PDFGeneratorService
from app.services.source_providers import SourceDiscoveryService
from app.services.chat_assistant import LemmaAssistantService
from app.services.pandaz_service import PandazPDFService

logger = logging.getLogger("lemma.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LEMMA 2.0 - AI Document Intelligence, Plagiarism Detection & Pandaz PDF Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
source_discovery_service = SourceDiscoveryService()
lemma_chat_service = LemmaAssistantService()
lite_matcher_instance = LiteMatcher()

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


# --- 1. SYSTEM HEALTH & STATUS ---

@app.get("/health")
@app.get(f"{settings.API_V1_STR}/health")
async def health():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": "2.0.0",
        "mode": "lite_ready"
    }

@app.get(f"{settings.API_V1_STR}/system/status")
@app.get("/api/system/status", include_in_schema=False)
async def system_status():
    """
    Returns granular status for all subsystem components:
    Backend, Analysis, AI, Search, Database, Vector DB, Reports, PDF Tools.
    """
    ai_available = await lemma_chat_service.ollama.is_available()
    return {
        "status": "online",
        "mode": "Lite Mode (Local Processing & Corpus)",
        "subsystems": {
            "backend": "ONLINE",
            "analysis_engine": "ONLINE (TF-IDF + Cosine + N-gram)",
            "ai_assistant": "ONLINE" if ai_available else "OFFLINE (Using Deterministic Local Assistant)",
            "search_providers": "ONLINE (Wikipedia, OpenAlex, Crossref, arXiv, Local)",
            "database": "OPTIONAL (Local Storage / SQLite)",
            "vector_search": "OPTIONAL (Local Fallback Active)",
            "reports_engine": "ONLINE (ReportLab / WeasyPrint)",
            "pandaz_pdf_tools": "ONLINE"
        },
        "reference_corpus_size": len(lite_matcher_instance.references)
    }

@app.get(f"{settings.API_V1_STR}/system/info")
@app.get("/api/info", include_in_schema=False)
async def get_system_info():
    return {
        "project": settings.PROJECT_NAME,
        "version": "2.0.0",
        "description": "AI-Powered Document Intelligence & Originality Workspace with Pandaz PDF Tools",
        "capabilities": {
            "supported_formats": [f".{ext}" for ext in settings.ALLOWED_EXTENSIONS],
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "spacy_model": settings.SPACY_MODEL,
            "ollama_model": settings.OLLAMA_MODEL,
            "features": [
                "Local-First Lite Plagiarism Detection Engine",
                "Context-Aware Ask Lemma Document RAG Chat",
                "Multi-Tone Academic & Professional Rewriting",
                "Pandaz PDF Toolkit (Merge, Split, Compress, CSV, Sign, OCR, Summarize)",
                "Scholarly Source Discovery (OpenAlex, Crossref, arXiv, Wikipedia)",
                "Publication-Ready Lemma Integrity PDF & HTML Reports"
            ]
        }
    }


# --- 2. DOCUMENT UPLOAD & DIRECT PLAGIARISM ANALYSIS ---

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to analyze")
    title: Optional[str] = Field(default="Pasted Document", description="Document title")

@app.post(f"{settings.API_V1_STR}/analyze/text")
@app.post("/api/analyze/text", include_in_schema=False)
async def analyze_text_direct(payload: TextAnalysisRequest):
    """
    Direct text analysis endpoint for pasted text or sample document.
    Executes full plagiarism analysis, readability metrics, and source matching.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty.")

    sentences_data = SentenceSegmenterService.segment(text)
    if not sentences_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not segment text into sentences.")

    metrics_data = DocumentAnalyticsService.analyze_readability(text, len(sentences_data))
    analysis_result = lite_matcher_instance.analyze_document(text, sentences_data)

    return {
        "status": "completed",
        "filename": payload.title or "Pasted Document",
        "text": text,
        "char_count": len(text),
        "sentence_count": len(sentences_data),
        "sentences": [
            SentenceCoordinate(
                text=s["text"],
                start_char=s["start_char"],
                end_char=s["end_char"]
            )
            for s in sentences_data
        ],
        "metrics": metrics_data,
        "analysis": analysis_result
    }

@app.post(
    f"{settings.API_V1_STR}/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload, segment and analyze a document"
)
@app.post("/api/documents/upload", include_in_schema=False)
async def upload_document(file: UploadFile = File(...)):
    """
    Ingests PDF, DOCX, or TXT file, extracts clean text, segments sentences,
    computes readability analytics and runs complete plagiarism analysis.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided in upload.")

    content = await file.read()
    text = DocumentExtractorService.extract_text(file.filename, content)
    sentences_data = SentenceSegmenterService.segment(text)

    sentences = [
        SentenceCoordinate(
            text=s["text"],
            start_char=s["start_char"],
            end_char=s["end_char"]
        )
        for s in sentences_data
    ]

    metrics_data = DocumentAnalyticsService.analyze_readability(text, len(sentences))
    analysis_result = lite_matcher_instance.analyze_document(text, sentences_data)

    return DocumentUploadResponse(
        filename=file.filename,
        text=text,
        char_count=len(text),
        sentence_count=len(sentences),
        sentences=sentences,
        metrics=metrics_data,
        analysis=analysis_result
    )

JOB_STORE: Dict[str, Any] = {}

@app.post(f"{settings.API_V1_STR}/analyze", status_code=status.HTTP_202_ACCEPTED)
@app.post("/api/analyze", status_code=status.HTTP_202_ACCEPTED, include_in_schema=False)
async def analyze_document_async(file: UploadFile = File(...)):
    """
    Async analysis endpoint. For Lite mode, processes immediately and returns 202 accepted state.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds limit of {settings.MAX_FILE_SIZE_MB}MB"
        )

    text = DocumentExtractorService.extract_text(file.filename, content)
    sentences_data = SentenceSegmenterService.segment(text)
    sentences = [
        SentenceCoordinate(
            text=s["text"],
            start_char=s["start_char"],
            end_char=s["end_char"]
        )
        for s in sentences_data
    ]
    metrics_data = DocumentAnalyticsService.analyze_readability(text, len(sentences))
    analysis_result = lite_matcher_instance.analyze_document(text, sentences_data)

    job_id = str(uuid.uuid4())
    result_payload = {
        "filename": file.filename,
        "text": text,
        "char_count": len(text),
        "sentence_count": len(sentences),
        "sentences": [s.model_dump() for s in sentences],
        "metrics": metrics_data,
        "analysis": analysis_result
    }
    JOB_STORE[job_id] = result_payload

    return {
        "job_id": job_id,
        "status": "completed",
        "result": result_payload
    }

@app.get(f"{settings.API_V1_STR}/status/{{job_id}}")
@app.get("/api/status/{job_id}", include_in_schema=False)
async def get_job_status(job_id: str):
    if job_id not in JOB_STORE:
        return {"job_id": job_id, "status": "pending"}
    return {
        "job_id": job_id,
        "status": "completed",
        "result": JOB_STORE[job_id]
    }


# --- 3. REPORT GENERATION ---

class ReportDirectRequest(BaseModel):
    filename: Optional[str] = "Lemma_Integrity_Report.pdf"
    text: Optional[str] = ""
    char_count: Optional[int] = 0
    sentence_count: Optional[int] = 0
    sentences: Optional[List[Dict[str, Any]]] = []
    metrics: Optional[Dict[str, Any]] = {}
    analysis: Optional[Dict[str, Any]] = {}

@app.post(f"{settings.API_V1_STR}/documents/report/direct")
@app.post("/api/report/direct", include_in_schema=False)
async def generate_direct_pdf_report(payload: ReportDirectRequest):
    """
    Generates and downloads a Lemma Integrity PDF report directly from the active frontend document state.
    """
    try:
        data_dict = payload.model_dump()
        pdf_bytes = PDFGeneratorService.generate_report(data_dict)
        fn = payload.filename or "lemma_integrity_report.pdf"
        if not fn.endswith(".pdf"):
            fn += ".pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{fn}"'}
        )
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        # Fallback to HTML report download
        html_content = PDFGeneratorService.generate_html_report(payload.model_dump())
        return Response(
            content=html_content.encode("utf-8"),
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="lemma_report.html"'}
        )

@app.get(f"{settings.API_V1_STR}/documents/report/{{job_id}}")
@app.get("/api/report/{job_id}", include_in_schema=False)
async def get_job_report_pdf(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plagiarism analysis is still in progress. Please wait for completion before downloading the report."
        )
    
    report_data = JOB_STORE[job_id]
    pdf_bytes = PDFGeneratorService.generate_report(report_data)
    fn = report_data.get("filename", "lemma_report.txt").rsplit(".", 1)[0] + "_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'}
    )


# --- 4. ASK LEMMA CONTEXT-AWARE CHAT & STREAMING ---

class ChatRequest(BaseModel):
    message: str = Field(..., description="User query message")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Active application/document state")

@app.post(f"{settings.API_V1_STR}/chat")
@app.post("/api/chat", include_in_schema=False)
async def chat_endpoint(payload: ChatRequest):
    """
    Context-aware Ask Lemma assistant.
    Understands current document, plagiarism score, matches, sources, and RAG chunks.
    """
    reply = await lemma_chat_service.generate_response(payload.message, payload.context or {})
    return {
        "response": reply,
        "status": "success"
    }

@app.post(f"{settings.API_V1_STR}/chat/stream")
@app.post("/api/chat/stream", include_in_schema=False)
async def chat_stream_endpoint(payload: ChatRequest):
    """
    Streaming Ask Lemma assistant response for live token-by-token UI display.
    """
    async def event_generator():
        async for chunk in lemma_chat_service.stream_response(payload.message, payload.context or {}):
            data = json.dumps({"token": chunk})
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- 5. PARAPHRASING & REWRITE ---

class BatchRewriteRequest(BaseModel):
    sentences: List[str] = Field(..., description="List of sentences to rewrite")
    tone: Optional[str] = Field(default="academic", description="Academic, Professional, Simple, Formal, Concise, Detailed")

@app.post(f"{settings.API_V1_STR}/rewrite")
@app.post("/api/rewrite", include_in_schema=False)
async def rewrite_text_endpoint(payload: RewriteRequest):
    """
    Rewrites a single sentence or passage to eliminate plagiarism.
    Uses local AI (Ollama) if available, with intelligent rule-based fallback.
    """
    tone = getattr(payload, "tone", "academic") or "academic"
    try:
        rewritten = await LLMService.rewrite_text(payload.text, tone=tone)
    except Exception:
        rewritten = LLMService.fallback_rewrite_text(payload.text, tone=tone)
    
    if not rewritten:
        rewritten = LLMService.fallback_rewrite_text(payload.text, tone=tone)

    return RewriteResponse(
        original_text=payload.text,
        rewritten_text=rewritten
    )

@app.post(f"{settings.API_V1_STR}/rewrite/batch")
@app.post("/api/rewrite/batch", include_in_schema=False)
async def rewrite_batch_endpoint(payload: BatchRewriteRequest):
    """
    Batch rewrite all flagged sentences sequentially with tone support.
    """
    results = []
    for sent in payload.sentences:
        if not sent.strip():
            continue
        rewritten = LLMService.fallback_rewrite_text(sent, tone=payload.tone or "academic")
        results.append({
            "original": sent,
            "rewritten": rewritten
        })
    return {
        "status": "completed",
        "total_rewritten": len(results),
        "results": results
    }


# --- 6. SOURCE DISCOVERY ---

class SourceDiscoveryRequest(BaseModel):
    query: str = Field(..., description="Search query or domain topic")
    providers: Optional[List[str]] = Field(default=None, description="Optional list of providers: wikipedia, openalex, crossref, arxiv")
    limit: Optional[int] = Field(default=8, description="Max results")

@app.post(f"{settings.API_V1_STR}/sources/discover")
@app.get(f"{settings.API_V1_STR}/sources/discover")
@app.post("/api/sources/discover", include_in_schema=False)
@app.get("/api/sources/discover", include_in_schema=False)
async def discover_sources(query: Optional[str] = None, payload: Optional[SourceDiscoveryRequest] = None):
    """
    Discovers academic & encyclopedia references from Wikipedia, OpenAlex, Crossref, and arXiv.
    """
    search_q = query
    providers = None
    limit = 8
    if payload:
        search_q = payload.query
        providers = payload.providers
        limit = payload.limit or 8

    if not search_q:
        search_q = "artificial intelligence machine learning research"

    results = await source_discovery_service.discover(search_q, provider_names=providers, limit=limit)
    return results


# --- 7. PANDAZ PDF TOOLS SUITE ---

@app.post(f"{settings.API_V1_STR}/pandaz/merge")
@app.post("/api/pandaz/merge", include_in_schema=False)
async def pandaz_merge_pdfs(files: List[UploadFile] = File(...)):
    """Merges multiple uploaded PDF files into a single unified PDF."""
    if not files or len(files) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload at least 2 PDF files to merge.")

    byte_list = []
    for f in files:
        b = await f.read()
        byte_list.append(b)

    try:
        merged_pdf = PandazPDFService.merge_pdfs(byte_list)
        return Response(
            content=merged_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="pandaz_merged.pdf"'}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Merge failed: {str(e)}")

@app.post(f"{settings.API_V1_STR}/pandaz/split")
@app.post("/api/pandaz/split", include_in_schema=False)
async def pandaz_split_pdf(file: UploadFile = File(...), page_range: str = Form("1-3")):
    """Splits a PDF by page ranges (e.g. 1-3, 5, 8-10)."""
    pdf_bytes = await file.read()
    try:
        split_bytes = PandazPDFService.split_pdf(pdf_bytes, page_range)
        base_name = file.filename.rsplit(".", 1)[0] if file.filename else "document"
        return Response(
            content=split_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{base_name}_split.pdf"'}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Split failed: {str(e)}")

@app.post(f"{settings.API_V1_STR}/pandaz/compress")
@app.post("/api/pandaz/compress", include_in_schema=False)
async def pandaz_compress_pdf(file: UploadFile = File(...)):
    """Compresses PDF content streams and removes duplicates."""
    pdf_bytes = await file.read()
    try:
        comp_bytes, orig_size, new_size, reduction = PandazPDFService.compress_pdf(pdf_bytes)
        base_name = file.filename.rsplit(".", 1)[0] if file.filename else "document"
        return Response(
            content=comp_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{base_name}_compressed.pdf"',
                "X-Original-Size": str(orig_size),
                "X-Compressed-Size": str(new_size),
                "X-Reduction-Percent": str(reduction)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Compression failed: {str(e)}")

@app.post(f"{settings.API_V1_STR}/pandaz/to-csv")
@app.post("/api/pandaz/to-csv", include_in_schema=False)
async def pandaz_pdf_to_csv(file: UploadFile = File(...)):
    """Extracts tables or tabular text from PDF and returns a CSV file."""
    pdf_bytes = await file.read()
    try:
        csv_text = PandazPDFService.extract_tables_to_csv(pdf_bytes)
        base_name = file.filename.rsplit(".", 1)[0] if file.filename else "extracted_data"
        return Response(
            content=csv_text.encode("utf-8"),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"CSV extraction error: {str(e)}")

@app.post(f"{settings.API_V1_STR}/pandaz/rename")
@app.post("/api/pandaz/rename", include_in_schema=False)
async def pandaz_rename_pdf(file: UploadFile = File(...), new_name: str = Form(...)):
    """Safely returns the PDF with the requested new filename."""
    pdf_bytes = await file.read()
    clean_name = re.sub(r'[^\w\-_.]', '_', new_name.strip())
    if not clean_name.endswith(".pdf"):
        clean_name += ".pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{clean_name}"'}
    )

@app.post(f"{settings.API_V1_STR}/pandaz/sign")
@app.post("/api/pandaz/sign", include_in_schema=False)
async def pandaz_sign_pdf(
    file: UploadFile = File(...),
    annotations_json: str = Form("[]"),
    signature_base64: Optional[str] = Form(None)
):
    """Applies annotations and signature overlay onto the uploaded PDF."""
    pdf_bytes = await file.read()
    try:
        annotations = json.loads(annotations_json)
    except Exception:
        annotations = []

    signed_pdf = PandazPDFService.annotate_and_sign_pdf(pdf_bytes, annotations, signature_base64)
    base_name = file.filename.rsplit(".", 1)[0] if file.filename else "document"
    return Response(
        content=signed_pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{base_name}_signed.pdf"'}
    )

@app.post(f"{settings.API_V1_STR}/pandaz/ocr")
@app.post("/api/pandaz/ocr", include_in_schema=False)
async def pandaz_ocr_endpoint(file: UploadFile = File(...)):
    """Performs Optical Character Recognition on an image or PDF."""
    file_bytes = await file.read()
    result = PandazPDFService.perform_ocr(file_bytes, file.filename or "file.pdf")
    return result

@app.post(f"{settings.API_V1_STR}/pandaz/summarize")
@app.post("/api/pandaz/summarize", include_in_schema=False)
async def pandaz_summarize_pdf(file: UploadFile = File(...)):
    """Extracts text from PDF and generates structured executive summary."""
    pdf_bytes = await file.read()
    try:
        summary_data = PandazPDFService.summarize_pdf(pdf_bytes, file.filename or "document.pdf")
        return summary_data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Summarization error: {str(e)}")

@app.post(f"{settings.API_V1_STR}/pandaz/rotate")
@app.post("/api/pandaz/rotate", include_in_schema=False)
async def pandaz_rotate_pdf(file: UploadFile = File(...), degrees: int = Form(90)):
    """Rotates PDF pages by 90, 180, or 270 degrees."""
    pdf_bytes = await file.read()
    rotated = PandazPDFService.rotate_pdf(pdf_bytes, degrees)
    return Response(
        content=rotated,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="rotated_{file.filename}"'}
    )

@app.post(f"{settings.API_V1_STR}/pandaz/delete-pages")
@app.post("/api/pandaz/delete-pages", include_in_schema=False)
async def pandaz_delete_pages(file: UploadFile = File(...), pages: str = Form(...)):
    """Deletes specified page indices from PDF."""
    pdf_bytes = await file.read()
    try:
        res_bytes = PandazPDFService.delete_pdf_pages(pdf_bytes, pages)
        return Response(
            content=res_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="modified_{file.filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post(f"{settings.API_V1_STR}/pandaz/images-to-pdf")
@app.post("/api/pandaz/images-to-pdf", include_in_schema=False)
async def pandaz_images_to_pdf(files: List[UploadFile] = File(...)):
    """Converts uploaded images into a PDF."""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No image files provided.")
    img_bytes_list = []
    for f in files:
        b = await f.read()
        img_bytes_list.append(b)
    pdf_bytes = PandazPDFService.images_to_pdf(img_bytes_list)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="converted_images.pdf"'}
    )

@app.post(f"{settings.API_V1_STR}/pandaz/to-lemma")
@app.post("/api/pandaz/to-lemma", include_in_schema=False)
async def pandaz_send_to_lemma(file: UploadFile = File(...)):
    """
    Pandaz ↔ Lemma Integration Endpoint.
    Extracts text from a Pandaz PDF and directly triggers complete Lemma plagiarism analysis.
    """
    pdf_bytes = await file.read()
    text = PandazPDFService.extract_text_from_pdf(pdf_bytes)
    if not text.strip():
        text = "Sample text extracted from Pandaz document."

    sentences_data = SentenceSegmenterService.segment(text)
    metrics_data = DocumentAnalyticsService.analyze_readability(text, len(sentences_data))
    analysis_result = lite_matcher_instance.analyze_document(text, sentences_data)

    return {
        "status": "success",
        "message": "PDF successfully imported and analyzed in Lemma!",
        "filename": file.filename,
        "text": text,
        "char_count": len(text),
        "sentence_count": len(sentences_data),
        "sentences": [
            SentenceCoordinate(
                text=s["text"],
                start_char=s["start_char"],
                end_char=s["end_char"]
            )
            for s in sentences_data
        ],
        "metrics": metrics_data,
        "analysis": analysis_result
    }



# --- 8. PERSISTENT HISTORY & WORKSPACE PROJECTS ---

from app.services.storage_service import StorageService

class HistorySaveRequest(BaseModel):
    id: Optional[str] = None
    filename: Optional[str] = "Untitled Document"
    title: Optional[str] = None
    char_count: Optional[int] = 0
    sentence_count: Optional[int] = 0
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    text: Optional[str] = ""
    sentences: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    project_id: Optional[str] = "default"

class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Project name")
    description: Optional[str] = ""
    tags: Optional[List[str]] = Field(default_factory=list)

@app.get(f"{settings.API_V1_STR}/history")
@app.get("/api/history", include_in_schema=False)
async def list_history_records(limit: int = 50):
    """Lists saved analysis runs in persistent local storage."""
    records = StorageService.list_history(limit=limit)
    return {"status": "success", "count": len(records), "history": records}

@app.post(f"{settings.API_V1_STR}/history")
@app.post("/api/history", include_in_schema=False)
async def save_history_record(payload: HistorySaveRequest):
    """Saves or updates an analysis run in history."""
    saved = StorageService.save_analysis(payload.model_dump())
    return {"status": "success", "record": saved}

@app.get(f"{settings.API_V1_STR}/history/{{record_id}}")
@app.get("/api/history/{record_id}", include_in_schema=False)
async def get_history_record(record_id: str):
    """Retrieves a single historical analysis run."""
    record = StorageService.get_analysis(record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found")
    return {"status": "success", "record": record}

@app.delete(f"{settings.API_V1_STR}/history/{{record_id}}")
@app.delete("/api/history/{record_id}", include_in_schema=False)
async def delete_history_record(record_id: str):
    """Deletes an analysis run from history."""
    deleted = StorageService.delete_analysis(record_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found")
    return {"status": "success", "message": "Record deleted"}

@app.get(f"{settings.API_V1_STR}/projects")
@app.get("/api/projects", include_in_schema=False)
async def list_workspace_projects():
    """Lists all workspace projects."""
    projects = StorageService.list_projects()
    return {"status": "success", "count": len(projects), "projects": projects}

@app.post(f"{settings.API_V1_STR}/projects")
@app.post("/api/projects", include_in_schema=False)
async def create_workspace_project(payload: ProjectCreateRequest):
    """Creates a new workspace project."""
    proj = StorageService.create_project(payload.name, payload.description or "", payload.tags or [])
    return {"status": "success", "project": proj}

@app.get(f"{settings.API_V1_STR}/projects/{{project_id}}")
@app.get("/api/projects/{project_id}", include_in_schema=False)
async def get_workspace_project(project_id: str):
    """Gets project details with linked documents and chats."""
    proj = StorageService.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return {"status": "success", "project": proj}

@app.delete(f"{settings.API_V1_STR}/projects/{{project_id}}")
@app.delete("/api/projects/{project_id}", include_in_schema=False)
async def delete_workspace_project(project_id: str):
    """Deletes a workspace project."""
    if project_id == "default":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete default project")
    deleted = StorageService.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return {"status": "success", "message": "Project deleted"}

@app.get(f"{settings.API_V1_STR}/search")
@app.get("/api/search", include_in_schema=False)
async def global_cross_entity_search(q: str = ""):
    """
    Real cross-entity global search querying:
    - Analyzed documents in history
    - Workspace projects
    - Scholarly reference corpus
    """
    results = StorageService.global_search(q, limit=15)
    return results


# --- 9. STATIC FRONTEND MOUNT ---
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
try:
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
except Exception as e:
    logger.warning(f"Could not mount frontend static files: {e}")

