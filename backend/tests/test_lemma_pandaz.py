import io
import pytest
from pypdf import PdfWriter, PdfReader
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_dummy_pdf(text: str = "Deep learning is a subset of machine learning based on artificial neural networks.") -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 700, text)
    c.drawString(100, 650, "Here is a second sentence for testing document splitting and summarization.")
    c.showPage()
    c.drawString(100, 700, "Page 2 content for split and merge testing.")
    c.save()
    return buf.getvalue()

def test_health_and_system_status():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res_status = client.get("/api/v1/system/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "subsystems" in data
    assert data["subsystems"]["backend"] == "ONLINE"
    assert data["subsystems"]["pandaz_pdf_tools"] == "ONLINE"

def test_direct_text_analysis():
    # Text matching ref_tech_deep_learning from local corpus
    sample_text = (
        "Deep learning is a subset of machine learning that is based on artificial neural networks with representation learning. "
        "This is an entirely unique sentence created by the user for testing originality."
    )
    res = client.post("/api/v1/analyze/text", json={"text": sample_text, "title": "Test Deep Learning Doc"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert "plagiarism_score" in data["analysis"]
    assert "originality_score" in data["analysis"]
    assert data["analysis"]["plagiarism_score"] > 0
    assert len(data["analysis"]["matches"]) >= 1
    assert "metrics" in data
    assert data["metrics"]["word_count"] > 0

def test_document_upload_txt():
    content = b"The World Wide Web was invented by Sir Tim Berners-Lee in 1989 while working at CERN as a distributed information sharing system."
    res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("history.txt", content, "text/plain")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "history.txt"
    assert data["char_count"] > 0
    assert data["analysis"] is not None
    assert data["analysis"]["plagiarism_score"] > 0

def test_rewrite_single_and_batch():
    text = "Deep learning needs strong computing to make good models."
    res = client.post("/api/v1/rewrite", json={"text": text, "tone": "academic"})
    assert res.status_code == 200
    data = res.json()
    assert "rewritten_text" in data
    assert len(data["rewritten_text"]) > 0

    batch_res = client.post(
        "/api/v1/rewrite/batch",
        json={"sentences": [text, "This is another sentence."], "tone": "formal"}
    )
    assert batch_res.status_code == 200
    assert batch_res.json()["total_rewritten"] == 2

def test_ask_lemma_chat():
    context = {
        "text": "Deep learning is a subset of machine learning.",
        "analysis": {
            "plagiarism_score": 45.5,
            "originality_score": 54.5,
            "matched_sentences_count": 1,
            "total_sentences": 2,
            "matches": [
                {
                    "query_text": "Deep learning is a subset of machine learning.",
                    "matched_sentence": "Deep learning is a subset of machine learning that is based on artificial neural networks.",
                    "source": "Deep Learning Principles",
                    "similarity": 0.88,
                    "match_type": "lexical"
                }
            ],
            "sources": [{"title": "Deep Learning Principles", "author": "Dr. Jenkins", "match_count": 1, "max_similarity": 0.88}]
        }
    }
    
    # Test plagiarism score query
    res = client.post("/api/v1/chat", json={"message": "What is my plagiarism score?", "context": context})
    assert res.status_code == 200
    assert "45.5%" in res.json()["response"]

    # Test top sources query
    res_src = client.post("/api/v1/chat", json={"message": "Show my top sources", "context": context})
    assert res_src.status_code == 200
    assert "Deep Learning Principles" in res_src.json()["response"]

def test_source_discovery():
    res = client.post("/api/v1/sources/discover", json={"query": "climate change clean energy", "limit": 4})
    assert res.status_code == 200
    data = res.json()
    assert "sources" in data
    assert len(data["sources"]) > 0

def test_direct_pdf_report_generation():
    payload = {
        "filename": "sample_document.pdf",
        "text": "Test document text for report.",
        "char_count": 30,
        "sentence_count": 1,
        "sentences": [{"text": "Test document text for report.", "start_char": 0, "end_char": 30}],
        "analysis": {
            "plagiarism_score": 25.0,
            "originality_score": 75.0,
            "matches": [],
            "sources": []
        }
    }
    res = client.post("/api/v1/documents/report/direct", json=payload)
    assert res.status_code == 200
    assert res.content.startswith(b"%PDF") or b"<html" in res.content.lower()

def test_pandaz_merge_split_compress():
    pdf1 = create_dummy_pdf("First document content")
    pdf2 = create_dummy_pdf("Second document content")

    # 1. Merge
    res_merge = client.post(
        "/api/v1/pandaz/merge",
        files=[("files", ("doc1.pdf", pdf1, "application/pdf")), ("files", ("doc2.pdf", pdf2, "application/pdf"))]
    )
    assert res_merge.status_code == 200
    merged_pdf_bytes = res_merge.content
    assert merged_pdf_bytes.startswith(b"%PDF")
    reader = PdfReader(io.BytesIO(merged_pdf_bytes))
    assert len(reader.pages) == 4

    # 2. Split (keep page 1 only)
    res_split = client.post(
        "/api/v1/pandaz/split",
        files={"file": ("merged.pdf", merged_pdf_bytes, "application/pdf")},
        data={"page_range": "1"}
    )
    assert res_split.status_code == 200
    split_reader = PdfReader(io.BytesIO(res_split.content))
    assert len(split_reader.pages) == 1

    # 3. Compress
    res_comp = client.post(
        "/api/v1/pandaz/compress",
        files={"file": ("merged.pdf", merged_pdf_bytes, "application/pdf")}
    )
    assert res_comp.status_code == 200
    assert res_comp.content.startswith(b"%PDF")

def test_pandaz_to_csv_and_summarize():
    pdf_bytes = create_dummy_pdf()
    
    # 1. Summarize
    res_sum = client.post(
        "/api/v1/pandaz/summarize",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")}
    )
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert "tldr" in sum_data
    assert "key_points" in sum_data

    # 2. To CSV
    res_csv = client.post(
        "/api/v1/pandaz/to-csv",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")}
    )
    assert res_csv.status_code == 200
    assert len(res_csv.text) > 0

def test_pandaz_to_lemma():
    pdf_bytes = create_dummy_pdf()
    res = client.post(
        "/api/v1/pandaz/to-lemma",
        files={"file": ("pandaz_import.pdf", pdf_bytes, "application/pdf")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "analysis" in data
    assert "metrics" in data
