"""
Lite Mode Plagiarism Matcher - TF-IDF based local matching
Works without PostgreSQL, Elasticsearch, or any external dependencies
"""

import json
import logging
import difflib
from pathlib import Path
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class LiteMatcher:
    """
    Local TF-IDF based plagiarism matcher.
    Loads references from mock_references.json and performs lexical/semantic matching.
    """

    def __init__(self):
        self.references = []
        self.reference_sentences = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.semantic_model = None
        self._load_references()

    def _load_references(self):
        """Load reference corpus from JSON file."""
        if not Path(settings.MOCK_DATABASE_PATH).exists():
            logger.warning(f"Mock references file not found at: {settings.MOCK_DATABASE_PATH}")
            return

        try:
            with open(settings.MOCK_DATABASE_PATH, "r", encoding="utf-8") as f:
                self.references = json.load(f)
            logger.info(f"Loaded {len(self.references)} reference documents")
        except Exception as e:
            logger.error(f"Failed to load references: {e}")
            self.references = []

    def _segment_and_flatten(self):
        """Segment all reference documents into sentences and flatten."""
        from app.services.segmenter import SentenceSegmenterService

        flat_sentences = []
        for doc in self.references:
            sentences = SentenceSegmenterService.segment(doc.get("text", ""))
            for idx, sent in enumerate(sentences):
                flat_sentences.append({
                    "text": sent["text"],
                    "doc_id": doc["id"],
                    "doc_title": doc.get("title", "Unknown"),
                    "doc_author": doc.get("author", "N/A"),
                    "doc_source": doc.get("source", "N/A"),
                    "sentence_index": idx,
                })
        return flat_sentences

    def _build_tfidf_index(self):
        """Build TF-IDF vectorizer and matrix from reference sentences."""
        if not self.reference_sentences:
            self.reference_sentences = self._segment_and_flatten()

        if not self.reference_sentences:
            logger.warning("No reference sentences to index")
            return

        corpus = [s["text"] for s in self.reference_sentences]
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        logger.info(f"Built TF-IDF index for {len(self.reference_sentences)} sentences")

    def _load_semantic_model(self):
        """Load SentenceTransformer model for semantic matching (optional)."""
        try:
            from sentence_transformers import SentenceTransformer
            if self.semantic_model is None:
                self.semantic_model = SentenceTransformer(settings.SENTENCE_TRANSFORMERS_MODEL)
                logger.info("Loaded SentenceTransformer model")
        except (ImportError, OSError) as e:
            logger.warning(f"SentenceTransformer unavailable: {e}. Semantic matching disabled.")
            self.semantic_model = None

    def find_lexical_matches(
        self, 
        query_text: str, 
        threshold: float = None,
        top_k: int = 5
    ) -> list[dict]:
        """
        Find lexical (TF-IDF based) matches for query text.
        Returns list of match dicts with score, text, source info.
        """
        if threshold is None:
            threshold = getattr(settings, 'LEXICAL_THRESHOLD', 0.4)

        if self.tfidf_matrix is None:
            self._build_tfidf_index()

        if not self.reference_sentences or self.tfidf_matrix is None:
            logger.warning("No TF-IDF index available")
            return []

        try:
            # Vectorize query text
            query_vec = self.vectorizer.transform([query_text])
            # Calculate cosine similarity with all references
            similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
            
            # Get top matches
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            matches = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= threshold:
                    ref_sent = self.reference_sentences[idx]
                    # Calculate additional lexical similarity using difflib
                    lexical_sim = difflib.SequenceMatcher(
                        None, 
                        query_text.lower(), 
                        ref_sent["text"].lower()
                    ).ratio()
                    
                    matches.append({
                        "query_text": query_text,
                        "matched_text": ref_sent["text"],
                        "tfidf_score": score,
                        "lexical_score": lexical_sim,
                        "combined_score": (score + lexical_sim) / 2.0,
                        "match_type": "lexical",
                        "doc_id": ref_sent["doc_id"],
                        "doc_title": ref_sent["doc_title"],
                        "doc_author": ref_sent["doc_author"],
                        "doc_source": ref_sent["doc_source"],
                        "sentence_index": ref_sent["sentence_index"],
                    })
            
            return sorted(matches, key=lambda x: x["combined_score"], reverse=True)
        except Exception as e:
            logger.error(f"Lexical matching failed: {e}")
            return []

    def find_semantic_matches(
        self,
        query_text: str,
        threshold: float = None,
        top_k: int = 5
    ) -> list[dict]:
        """
        Find semantic (embedding-based) matches using SentenceTransformer.
        Falls back gracefully if model unavailable.
        """
        if threshold is None:
            threshold = getattr(settings, 'SEMANTIC_THRESHOLD', 0.5)

        self._load_semantic_model()

        if self.semantic_model is None:
            logger.debug("SentenceTransformer model not available, skipping semantic matching")
            return []

        if not self.reference_sentences:
            self.reference_sentences = self._segment_and_flatten()

        if not self.reference_sentences:
            return []

        try:
            # Encode query and all reference sentences
            query_embedding = self.semantic_model.encode([query_text])[0]
            ref_embeddings = self.semantic_model.encode([s["text"] for s in self.reference_sentences])

            # Calculate cosine similarity
            similarities = cosine_similarity([query_embedding], ref_embeddings)[0]
            
            # Get top matches
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            matches = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= threshold:
                    ref_sent = self.reference_sentences[idx]
                    matches.append({
                        "query_text": query_text,
                        "matched_text": ref_sent["text"],
                        "semantic_score": score,
                        "match_type": "semantic",
                        "doc_id": ref_sent["doc_id"],
                        "doc_title": ref_sent["doc_title"],
                        "doc_author": ref_sent["doc_author"],
                        "doc_source": ref_sent["doc_source"],
                        "sentence_index": ref_sent["sentence_index"],
                    })
            
            return sorted(matches, key=lambda x: x["semantic_score"], reverse=True)
        except Exception as e:
            logger.error(f"Semantic matching failed: {e}")
            return []

    def find_hybrid_matches(
        self,
        query_text: str,
        lex_threshold: float = None,
        sem_threshold: float = None,
        top_k: int = 5
    ) -> list[dict]:
        """
        Find hybrid matches combining lexical and semantic results.
        Merges and re-scores based on both methods.
        """
        lexical_matches = self.find_lexical_matches(query_text, lex_threshold, top_k * 2)
        semantic_matches = self.find_semantic_matches(query_text, sem_threshold, top_k * 2)

        # Combine matches by doc_id
        matches_dict = {}
        
        for m in lexical_matches:
            key = (m["doc_id"], m["doc_title"])
            if key not in matches_dict:
                matches_dict[key] = m
            else:
                matches_dict[key]["has_lexical"] = True

        for m in semantic_matches:
            key = (m["doc_id"], m["doc_title"])
            if key not in matches_dict:
                matches_dict[key] = m
            else:
                matches_dict[key]["has_semantic"] = True
                if "semantic_score" in m:
                    matches_dict[key]["semantic_score"] = m["semantic_score"]

        # Re-score as hybrid
        hybrid_matches = []
        for match in matches_dict.values():
            scores = []
            if "combined_score" in match:
                scores.append(match["combined_score"])
            if "semantic_score" in match:
                scores.append(match["semantic_score"])
            
            hybrid_score = np.mean(scores) if scores else 0.0
            match["match_type"] = "hybrid"
            match["hybrid_score"] = hybrid_score
            hybrid_matches.append(match)

        return sorted(hybrid_matches, key=lambda x: x.get("hybrid_score", 0), reverse=True)[:top_k]

    def extract_matching_phrases(self, query: str, ref: str, min_length: int = 4) -> list[dict]:
        """
        Extract and return matching character slices between query and reference.
        Returns list of dicts with start, end, and matched text.
        """
        matcher = difflib.SequenceMatcher(None, query.lower(), ref.lower())
        matching_blocks = matcher.get_matching_blocks()

        slices = []
        for block in matching_blocks:
            start_q, start_r, size = block
            if size >= min_length:
                matched_text = query[start_q : start_q + size]
                stripped_text = matched_text.strip()
                if stripped_text:
                    leading_spaces = len(matched_text) - len(matched_text.lstrip())
                    trailing_spaces = len(matched_text) - len(matched_text.rstrip())

                    final_start = start_q + leading_spaces
                    final_end = start_q + size - trailing_spaces

                    if (final_end - final_start) >= min_length:
                        slices.append({
                            "start": final_start,
                            "end": final_end,
                            "text": query[final_start:final_end]
                        })

        if not slices:
            return []

        slices.sort(key=lambda x: x["start"])
        merged = [slices[0]]
        for current in slices[1:]:
            prev = merged[-1]
            if current["start"] <= prev["end"] + 2:
                prev["end"] = max(prev["end"], current["end"])
                prev["text"] = query[prev["start"]:prev["end"]]
            else:
                merged.append(current)

        return merged
