"""
Structured Local Storage and Cross-Entity Search Service for Lemma 2.0.
Provides file-backed JSON/SQLite persistence for analysis history, workspace projects, and chat logs.
Operates seamlessly in zero-dependency Lite Mode.
"""

import os
import json
import uuid
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Manages persistent analysis history, workspace projects, and search indexing."""

    STORAGE_DIR = Path(settings.BASE_DIR) / "data" / "storage"
    HISTORY_FILE = STORAGE_DIR / "history.json"
    PROJECTS_FILE = STORAGE_DIR / "projects.json"
    CHATS_FILE = STORAGE_DIR / "chats.json"

    @classmethod
    def _ensure_storage_dir(cls):
        try:
            cls.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create storage dir {cls.STORAGE_DIR}: {e}")

    @classmethod
    def _read_json(cls, file_path: Path, default_factory=list) -> Any:
        cls._ensure_storage_dir()
        if not file_path.exists():
            return default_factory()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading JSON from {file_path}: {e}")
            return default_factory()

    @classmethod
    def _write_json(cls, file_path: Path, data: Any):
        cls._ensure_storage_dir()
        try:
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(file_path)
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")

    # --- HISTORY METHODS ---

    @classmethod
    def save_analysis(cls, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves an analysis run to the local history store."""
        history = cls._read_json(cls.HISTORY_FILE, list)
        
        record_id = analysis_data.get("id") or str(uuid.uuid4())
        record = {
            "id": record_id,
            "filename": analysis_data.get("filename", "Untitled Document"),
            "title": analysis_data.get("title") or analysis_data.get("filename", "Untitled Document"),
            "created_at": analysis_data.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": analysis_data.get("timestamp") or int(time.time()),
            "char_count": analysis_data.get("char_count", 0),
            "sentence_count": analysis_data.get("sentence_count", 0),
            "metrics": analysis_data.get("metrics", {}),
            "analysis": analysis_data.get("analysis", {}),
            "text": analysis_data.get("text", ""),
            "sentences": analysis_data.get("sentences", []),
            "project_id": analysis_data.get("project_id", "default")
        }

        # Remove existing record with same ID if updating
        history = [h for h in history if h.get("id") != record_id]
        history.insert(0, record)
        
        # Keep maximum 100 historical records in Lite Mode
        if len(history) > 100:
            history = history[:100]

        cls._write_json(cls.HISTORY_FILE, history)
        return record

    @classmethod
    def list_history(cls, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the list of saved analysis runs."""
        history = cls._read_json(cls.HISTORY_FILE, list)
        return history[:limit]

    @classmethod
    def get_analysis(cls, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single analysis run by ID."""
        history = cls._read_json(cls.HISTORY_FILE, list)
        for h in history:
            if h.get("id") == record_id:
                return h
        return None

    @classmethod
    def delete_analysis(cls, record_id: str) -> bool:
        """Deletes an analysis run by ID."""
        history = cls._read_json(cls.HISTORY_FILE, list)
        original_len = len(history)
        history = [h for h in history if h.get("id") != record_id]
        if len(history) < original_len:
            cls._write_json(cls.HISTORY_FILE, history)
            return True
        return False

    @classmethod
    def clear_history(cls) -> bool:
        cls._write_json(cls.HISTORY_FILE, [])
        return True

    # --- PROJECT / WORKSPACE METHODS ---

    @classmethod
    def list_projects(cls) -> List[Dict[str, Any]]:
        """Lists all workspace projects."""
        projects = cls._read_json(cls.PROJECTS_FILE, list)
        if not projects:
            # Seed standard default project
            default_project = {
                "id": "default",
                "name": "General Research",
                "description": "Default workspace project for document originality and intelligence.",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "document_count": 0,
                "tags": ["Academic", "Primary"]
            }
            projects = [default_project]
            cls._write_json(cls.PROJECTS_FILE, projects)
        return projects

    @classmethod
    def create_project(cls, name: str, description: str = "", tags: List[str] = None) -> Dict[str, Any]:
        """Creates a new workspace project."""
        projects = cls._read_json(cls.PROJECTS_FILE, list)
        proj_id = str(uuid.uuid4())[:8]
        proj = {
            "id": proj_id,
            "name": name.strip() or "Untitled Project",
            "description": description.strip(),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "document_count": 0,
            "tags": tags or ["Research"]
        }
        projects.insert(0, proj)
        cls._write_json(cls.PROJECTS_FILE, projects)
        return proj

    @classmethod
    def get_project(cls, project_id: str) -> Optional[Dict[str, Any]]:
        projects = cls.list_projects()
        for p in projects:
            if p.get("id") == project_id:
                # Attach linked history documents
                history = cls.list_history()
                linked_docs = [h for h in history if h.get("project_id") == project_id or (project_id == "default" and not h.get("project_id"))]
                p_copy = dict(p)
                p_copy["documents"] = linked_docs
                p_copy["document_count"] = len(linked_docs)
                return p_copy
        return None

    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        if project_id == "default":
            return False  # Cannot delete default project
        projects = cls._read_json(cls.PROJECTS_FILE, list)
        orig_len = len(projects)
        projects = [p for p in projects if p.get("id") != project_id]
        if len(projects) < orig_len:
            cls._write_json(cls.PROJECTS_FILE, projects)
            return True
        return False

    # --- CROSS-ENTITY SEARCH METHOD ---

    @classmethod
    def global_search(cls, query: str, limit: int = 15) -> Dict[str, Any]:
        """
        Executes real cross-entity search across:
        1. Analyzed Documents & History
        2. Workspace Projects
        3. Reference Corpus Sources
        """
        q = query.strip().lower()
        if not q:
            return {"query": "", "results": {"documents": [], "projects": [], "sources": []}, "total": 0}

        # 1. Search History & Documents
        history = cls.list_history()
        matched_docs = []
        for h in history:
            title = h.get("title", "")
            filename = h.get("filename", "")
            text = h.get("text", "")
            if q in title.lower() or q in filename.lower() or q in text.lower():
                # Extract matching snippet
                snippet = ""
                idx = text.lower().find(q)
                if idx != -1:
                    start = max(0, idx - 40)
                    end = min(len(text), idx + len(q) + 60)
                    snippet = "..." + text[start:end].replace("\n", " ") + "..."
                else:
                    snippet = text[:100] + "..." if len(text) > 100 else text

                score_val = h.get("analysis", {}).get("plagiarism_score", 0)
                matched_docs.append({
                    "id": h.get("id"),
                    "title": title or filename,
                    "filename": filename,
                    "snippet": snippet,
                    "created_at": h.get("created_at"),
                    "plagiarism_score": score_val,
                    "type": "document"
                })
                if len(matched_docs) >= limit:
                    break

        # 2. Search Projects
        projects = cls.list_projects()
        matched_projects = []
        for p in projects:
            p_name = p.get("name", "")
            p_desc = p.get("description", "")
            p_tags = " ".join(p.get("tags", []))
            if q in p_name.lower() or q in p_desc.lower() or q in p_tags.lower():
                matched_projects.append({
                    "id": p.get("id"),
                    "name": p_name,
                    "description": p_desc,
                    "tags": p.get("tags", []),
                    "type": "project"
                })
                if len(matched_projects) >= limit:
                    break

        # 3. Search Reference Sources Corpus
        from app.services.lite_matcher import LiteMatcher
        lm = LiteMatcher()
        matched_sources = []
        for ref in lm.references:
            r_title = ref.get("title", "")
            r_author = ref.get("author", "")
            r_source = ref.get("source", "")
            r_text = ref.get("text", "") or ref.get("content", "")
            if q in r_title.lower() or q in r_author.lower() or q in r_source.lower() or q in r_text.lower():
                matched_sources.append({
                    "id": ref.get("id"),
                    "title": r_title,
                    "author": r_author,
                    "source": r_source,
                    "category": ref.get("category", "General"),
                    "url": ref.get("url", ""),
                    "snippet": r_text[:120] + "..." if len(r_text) > 120 else r_text,
                    "type": "source"
                })
                if len(matched_sources) >= limit:
                    break

        total = len(matched_docs) + len(matched_projects) + len(matched_sources)
        return {
            "query": query,
            "total": total,
            "results": {
                "documents": matched_docs,
                "projects": matched_projects,
                "sources": matched_sources
            }
        }
