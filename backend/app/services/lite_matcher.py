"""
Lite Mode Plagiarism Matcher - TF-IDF & N-gram based local matching
Works completely offline without PostgreSQL, Elasticsearch, Redis, Celery, or Ollama.
"""

import json
import logging
import difflib
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class LiteMatcher:
    """
    Local TF-IDF & N-gram based plagiarism matcher.
    Loads references from references.json and performs lexical, semantic, and hybrid matching.
    """

    def __init__(self):
        self.references: List[Dict[str, Any]] = []
        self.reference_sentences: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.semantic_model = None
        self._load_references()

    def _load_references(self):
        """Load reference corpus from references.json or fallback mock_references.json."""
        ref_path = getattr(settings, "REFERENCES_PATH", None) or getattr(settings, "MOCK_DATABASE_PATH", None)
        
        candidates = [
            ref_path,
            Path(settings.BASE_DIR) / "data" / "references" / "references.json",
            Path(settings.BASE_DIR) / "data" / "mock_references.json",
        ]

        loaded = False
        for p in candidates:
            if p and Path(p).exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        self.references = json.load(f)
                    logger.info(f"Loaded {len(self.references)} reference documents from {p}")
                    loaded = True
                    break
                except Exception as e:
                    logger.error(f"Failed to load references from {p}: {e}")

        if not loaded:
            logger.warning("No reference file found, using built-in standard corpus")
            self.references = [
                {
                    "id": "ref_deep_learning",
                    "title": "Deep Learning: Principles and Foundations",
                    "author": "Dr. Sarah Jenkins",
                    "source": "Journal of Artificial Intelligence Research, 2024",
                    "url": "https://doi.org/10.1016/j.jair.2024.01.004",
                    "category": "Technology",
                    "text": "Deep learning is a subset of machine learning that is based on artificial neural networks with representation learning. The adjective deep in deep learning refers to the use of multiple layers in the network. Historically, neural networks were limited in depth due to computational constraints and training difficulties. Today, modern deep learning architectures utilize convolutional neural networks and transformer architectures to process vast datasets. These models have revolutionized fields like computer vision, natural language processing, and robotics."
                }
            ]

    def _segment_and_flatten(self) -> List[Dict[str, Any]]:
        """Segment all reference documents into sentences and flatten."""
        from app.services.segmenter import SentenceSegmenterService

        flat_sentences = []
        for doc in self.references:
            doc_text = doc.get("text", "") or doc.get("content", "")
            sentences = SentenceSegmenterService.segment(doc_text)
            for idx, sent in enumerate(sentences):
                flat_sentences.append({
                    "text": sent["text"],
                    "doc_id": doc.get("id", str(uuid.uuid4())),
                    "doc_title": doc.get("title", "Unknown"),
                    "doc_author": doc.get("author", "N/A"),
                    "doc_source": doc.get("source", "Reference Library"),
                    "doc_url": doc.get("url", ""),
                    "doc_category": doc.get("category", "General"),
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
            ngram_range=(1, 3),
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        logger.info(f"Built TF-IDF index for {len(self.reference_sentences)} reference sentences")

    def _load_semantic_model(self):
        """Lazy load SentenceTransformer model only if already available locally."""
        if self.semantic_model is not None:
            return
        # Do not download models in Lite Mode to guarantee instantaneous offline execution
        self.semantic_model = None

    def find_lexical_matches(
        self, 
        query_text: str, 
        threshold: Optional[float] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find lexical (TF-IDF + character sequence difflib) matches.
        """
        if threshold is None:
            threshold = getattr(settings, 'LEXICAL_THRESHOLD', 0.50)

        if self.tfidf_matrix is None:
            self._build_tfidf_index()

        if not self.reference_sentences or self.tfidf_matrix is None:
            return []

        try:
            query_vec = self.vectorizer.transform([query_text])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            matches = []
            for idx in top_indices:
                tfidf_score = float(similarities[idx])
                ref_sent = self.reference_sentences[idx]
                
                # difflib character/word ratio
                lexical_sim = difflib.SequenceMatcher(
                    None, 
                    query_text.lower(), 
                    ref_sent["text"].lower()
                ).ratio()
                
                combined = (tfidf_score * 0.6) + (lexical_sim * 0.4)
                
                if combined >= threshold or lexical_sim >= 0.65 or tfidf_score >= 0.70:
                    matches.append({
                        "query_text": query_text,
                        "matched_text": ref_sent["text"],
                        "tfidf_score": round(tfidf_score, 4),
                        "lexical_score": round(lexical_sim, 4),
                        "similarity": round(combined, 4),
                        "match_type": "lexical",
                        "doc_id": ref_sent["doc_id"],
                        "doc_title": ref_sent["doc_title"],
                        "doc_author": ref_sent["doc_author"],
                        "doc_source": ref_sent["doc_source"],
                        "doc_url": ref_sent["doc_url"],
                        "doc_category": ref_sent["doc_category"],
                        "sentence_index": ref_sent["sentence_index"],
                    })
            
            return sorted(matches, key=lambda x: x["similarity"], reverse=True)
        except Exception as e:
            logger.error(f"Lexical matching failed: {e}")
            return []

    def find_semantic_matches(
        self,
        query_text: str,
        threshold: Optional[float] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find semantic matches using embeddings if available.
        """
        if threshold is None:
            threshold = getattr(settings, 'SEMANTIC_THRESHOLD', 0.55)

        self._load_semantic_model()

        if self.semantic_model is None:
            return []

        if not self.reference_sentences:
            self.reference_sentences = self._segment_and_flatten()

        if not self.reference_sentences:
            return []

        try:
            query_embedding = self.semantic_model.encode([query_text])[0]
            ref_embeddings = self.semantic_model.encode([s["text"] for s in self.reference_sentences])

            similarities = cosine_similarity([query_embedding], ref_embeddings)[0]
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            matches = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= threshold:
                    ref_sent = self.reference_sentences[idx]
                    matches.append({
                        "query_text": query_text,
                        "matched_text": ref_sent["text"],
                        "semantic_score": round(score, 4),
                        "similarity": round(score, 4),
                        "match_type": "semantic",
                        "doc_id": ref_sent["doc_id"],
                        "doc_title": ref_sent["doc_title"],
                        "doc_author": ref_sent["doc_author"],
                        "doc_source": ref_sent["doc_source"],
                        "doc_url": ref_sent["doc_url"],
                        "doc_category": ref_sent["doc_category"],
                        "sentence_index": ref_sent["sentence_index"],
                    })
            
            return sorted(matches, key=lambda x: x["similarity"], reverse=True)
        except Exception as e:
            logger.error(f"Semantic matching failed: {e}")
            return []

    def find_hybrid_matches(
        self,
        query_text: str,
        lex_threshold: Optional[float] = None,
        sem_threshold: Optional[float] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find hybrid matches combining lexical and semantic results.
        """
        lexical_matches = self.find_lexical_matches(query_text, lex_threshold, top_k * 2)
        semantic_matches = self.find_semantic_matches(query_text, sem_threshold, top_k * 2)

        if not semantic_matches:
            return lexical_matches[:top_k]

        matches_dict = {}
        for m in lexical_matches:
            key = (m["doc_id"], m["matched_text"])
            matches_dict[key] = {**m, "has_lexical": True, "lexical_sim": m["similarity"]}

        for m in semantic_matches:
            key = (m["doc_id"], m["matched_text"])
            if key in matches_dict:
                matches_dict[key]["has_semantic"] = True
                matches_dict[key]["semantic_sim"] = m["similarity"]
                matches_dict[key]["match_type"] = "hybrid"
                matches_dict[key]["similarity"] = round((matches_dict[key]["lexical_sim"] + m["similarity"]) / 2.0, 4)
            else:
                matches_dict[key] = {**m, "has_semantic": True, "semantic_sim": m["similarity"]}

        return sorted(matches_dict.values(), key=lambda x: x.get("similarity", 0), reverse=True)[:top_k]

    def extract_matching_phrases(self, query: str, ref: str, min_length: int = 4) -> List[Dict[str, Any]]:
        """
        Extract matching character slices between query and reference for granular highlighting.
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

    def analyze_document(self, text: str, sentences_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform a comprehensive plagiarism and originality analysis over all segmented sentences.
        Returns complete plagiarism score, breakdown, highlights, and aggregated source cards.
        """
        all_matches = []
        lexical_count = 0
        semantic_count = 0
        hybrid_count = 0
        matched_words_count = 0
        total_words = len(text.split())

        sources_map: Dict[str, Dict[str, Any]] = {}

        for sent_idx, sent in enumerate(sentences_data):
            sent_text = sent["text"]
            sent_start = sent["start_char"]
            sent_end = sent["end_char"]

            matches = self.find_hybrid_matches(sent_text, top_k=3)
            if matches:
                best = matches[0]
                m_type = best.get("match_type", "lexical")
                if m_type == "lexical":
                    lexical_count += 1
                elif m_type == "semantic":
                    semantic_count += 1
                else:
                    hybrid_count += 1

                phrases = self.extract_matching_phrases(sent_text, best.get("matched_text", ""))
                match_id = f"match_{sent_idx}_{uuid.uuid4().hex[:6]}"

                # Count matched words in phrases
                for p in phrases:
                    matched_words_count += len(p["text"].split())

                match_obj = {
                    "id": match_id,
                    "sentence_index": sent_idx,
                    "query_sentence": {
                        "text": sent_text,
                        "start_char": sent_start,
                        "end_char": sent_end,
                    },
                    "matched_sentence": best.get("matched_text", ""),
                    "similarity": float(best.get("similarity", 0.0)),
                    "match_type": m_type,
                    "source": best.get("doc_title", "Unknown Reference"),
                    "source_author": best.get("doc_author", "Unknown"),
                    "source_url": best.get("doc_url", ""),
                    "source_publication": best.get("doc_source", ""),
                    "source_category": best.get("doc_category", "General"),
                    "start_position": sent_start,
                    "end_position": sent_end,
                    "highlights": [
                        {
                            "start_char": sent_start + p["start"],
                            "end_char": sent_start + p["end"],
                            "text": p["text"]
                        }
                        for p in phrases
                    ],
                    "phrases": phrases
                }
                all_matches.append(match_obj)

                # Group into sources
                source_key = best.get("doc_title", "Unknown Reference")
                if source_key not in sources_map:
                    sources_map[source_key] = {
                        "id": best.get("doc_id", source_key),
                        "title": best.get("doc_title", "Unknown Reference"),
                        "author": best.get("doc_author", "Unknown Author"),
                        "source": best.get("doc_source", "Reference Library"),
                        "url": best.get("doc_url", ""),
                        "category": best.get("doc_category", "General"),
                        "match_type": m_type,
                        "match_count": 0,
                        "max_similarity": 0.0,
                    }
                sources_map[source_key]["match_count"] += 1
                sources_map[source_key]["max_similarity"] = max(
                    sources_map[source_key]["max_similarity"],
                    float(best.get("similarity", 0.0))
                )

        total_sentences = len(sentences_data)
        matched_sentences_count = len(all_matches)

        if total_sentences > 0:
            plagiarism_score = (matched_sentences_count / total_sentences) * 100.0
        else:
            plagiarism_score = 0.0

        originality_score = max(0.0, 100.0 - plagiarism_score)

        # Build clean sorted sources list
        sources_list = sorted(
            sources_map.values(),
            key=lambda x: (x["match_count"], x["max_similarity"]),
            reverse=True
        )

        return {
            "plagiarism_score": round(plagiarism_score, 2),
            "originality_score": round(originality_score, 2),
            "total_sentences": total_sentences,
            "matched_sentences_count": matched_sentences_count,
            "matched_words": matched_words_count,
            "total_words": total_words,
            "lexical_matches_count": lexical_count,
            "semantic_matches_count": semantic_count,
            "hybrid_matches_count": hybrid_count,
            "matches": all_matches,
            "sources": sources_list,
            "mode": "lite"
        }
