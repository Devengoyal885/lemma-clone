import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage_service import StorageService

client = TestClient(app)

def test_storage_history_lifecycle():
    # 1. Save an analysis record
    record_data = {
        "title": "Quantum Computing Paper",
        "filename": "quantum.txt",
        "char_count": 500,
        "sentence_count": 5,
        "text": "Quantum computing utilizes superposition and entanglement to solve computational problems.",
        "analysis": {
            "plagiarism_score": 15.5,
            "originality_score": 84.5
        },
        "metrics": {
            "word_count": 80,
            "flesch_reading_ease": 65.0
        }
    }
    
    res = client.post("/api/v1/history", json=record_data)
    assert res.status_code == 200
    saved = res.json()["record"]
    rec_id = saved["id"]
    assert rec_id is not None
    assert saved["title"] == "Quantum Computing Paper"
    
    # 2. List history
    list_res = client.get("/api/v1/history")
    assert list_res.status_code == 200
    history = list_res.json()["history"]
    assert any(h["id"] == rec_id for h in history)
    
    # 3. Retrieve single record
    get_res = client.get(f"/api/v1/history/{rec_id}")
    assert get_res.status_code == 200
    assert get_res.json()["record"]["id"] == rec_id
    
    # 4. Global search includes this document
    search_res = client.get("/api/v1/search?q=superposition")
    assert search_res.status_code == 200
    s_data = search_res.json()
    assert s_data["total"] > 0
    assert any(d["id"] == rec_id for d in s_data["results"]["documents"])
    
    # 5. Delete record
    del_res = client.delete(f"/api/v1/history/{rec_id}")
    assert del_res.status_code == 200
    
    # Verify deletion
    get_deleted = client.get(f"/api/v1/history/{rec_id}")
    assert get_deleted.status_code == 404

def test_storage_project_lifecycle():
    # 1. List default projects
    res = client.get("/api/v1/projects")
    assert res.status_code == 200
    assert len(res.json()["projects"]) >= 1
    
    # 2. Create new project
    create_res = client.post("/api/v1/projects", json={
        "name": "Biochemistry Thesis",
        "description": "CRISPR and genetic engineering analysis",
        "tags": ["Biology", "Genetics"]
    })
    assert create_res.status_code == 200
    proj = create_res.json()["project"]
    proj_id = proj["id"]
    assert proj["name"] == "Biochemistry Thesis"
    
    # 3. Search finds project
    s_res = client.get("/api/v1/search?q=biochemistry")
    assert s_res.status_code == 200
    assert any(p["id"] == proj_id for p in s_res.json()["results"]["projects"])
    
    # 4. Get project details
    get_res = client.get(f"/api/v1/projects/{proj_id}")
    assert get_res.status_code == 200
    assert get_res.json()["project"]["name"] == "Biochemistry Thesis"
    
    # 5. Delete project
    del_res = client.delete(f"/api/v1/projects/{proj_id}")
    assert del_res.status_code == 200
