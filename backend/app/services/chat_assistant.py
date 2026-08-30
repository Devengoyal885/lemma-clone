"""
Ask Lemma - Context-Aware Document Intelligence & RAG Chat Assistant
Understands document state, analysis metrics, matches, sources, and provides RAG retrieval.
Supports Ollama (if available) with intelligent deterministic fallback.
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
import httpx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider:
    """Base interface for LLM / Generative providers."""
    async def generate_response(self, system_prompt: str, user_query: str) -> Optional[str]:
        raise NotImplementedError

    async def stream_response(self, system_prompt: str, user_query: str) -> AsyncGenerator[str, None]:
        raise NotImplementedError


class OllamaProvider(AIProvider):
    """Ollama local AI provider with timeout protection."""
    def __init__(self, base_url: str = settings.OLLAMA_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def is_available(self) -> bool:
        import socket
        import anyio
        def check_socket():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.15)
                    return s.connect_ex(("127.0.0.1", 11434)) == 0
            except Exception:
                return False
        return await anyio.to_thread.run_sync(check_socket)

    async def generate_response(self, system_prompt: str, user_query: str) -> Optional[str]:
        if not await self.is_available():
            return None

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"System: {system_prompt}\n\nUser: {user_query}\n\nAssistant:",
            "stream": False,
            "options": {"temperature": 0.4, "top_p": 0.9}
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
        return None

    async def stream_response(self, system_prompt: str, user_query: str) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"System: {system_prompt}\n\nUser: {user_query}\n\nAssistant:",
            "stream": True,
            "options": {"temperature": 0.4, "top_p": 0.9}
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as resp:
                    if resp.status_code == 200:
                        async for line in resp.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    chunk = data.get("response", "")
                                    if chunk:
                                        yield chunk
                                    if data.get("done", False):
                                        break
                                except Exception:
                                    continue
        except Exception as e:
            logger.warning(f"Ollama streaming failed: {e}")


class LemmaAssistantService:
    """
    Unified Context-Aware Assistant.
    Combines application context, document RAG, and deterministic reasoning.
    """

    def __init__(self):
        self.ollama = OllamaProvider()

    @staticmethod
    def _retrieve_relevant_chunks(document_text: str, query: str, top_k: int = 3) -> List[str]:
        """TF-IDF based lightweight RAG chunk retrieval."""
        if not document_text or not document_text.strip():
            return []

        # Chunk by paragraphs or multi-sentence blocks
        raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\r\n\r\n", document_text) if p.strip()]
        if not raw_paragraphs:
            raw_paragraphs = [document_text[i:i+400] for i in range(0, len(document_text), 350)]

        if not raw_paragraphs or not query.strip():
            return raw_paragraphs[:top_k]

        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf = vectorizer.fit_transform(raw_paragraphs)
            q_vec = vectorizer.transform([query])
            sims = cosine_similarity(q_vec, tfidf)[0]
            top_indices = sims.argsort()[::-1][:top_k]
            return [raw_paragraphs[i] for i in top_indices if sims[i] > 0.05] or raw_paragraphs[:top_k]
        except Exception:
            return raw_paragraphs[:top_k]

    @classmethod
    def answer_deterministic(cls, query: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Answers questions about document metrics, plagiarism, sources, and structure
        accurately using the true state data.
        """
        q = (query or "").lower().strip()
        doc_text = context.get("text", "") or context.get("document_text", "")
        analysis = context.get("analysis") or {}
        metrics = context.get("metrics") or analysis.get("metrics") or {}
        matches = context.get("matches") or analysis.get("matches") or []
        sources = context.get("sources") or analysis.get("sources") or []

        plag_score = analysis.get("plagiarism_score", 0.0)
        orig_score = analysis.get("originality_score", 100.0)
        total_sents = analysis.get("total_sentences", len(context.get("sentences", [])))
        matched_sents = analysis.get("matched_sentences_count", len(matches))
        word_count = metrics.get("word_count", len(doc_text.split()))
        reading_ease = metrics.get("flesch_reading_ease", "N/A")
        grade_level = metrics.get("flesch_kincaid_grade", "N/A")

        # 1. Plagiarism & Originality Score
        if any(w in q for w in ["plagiarism score", "plagiarism rate", "how much plagiar", "similarity score", "percent plagiar"]):
            return (
                f"📊 **Plagiarism Analysis Result**\n\n"
                f"- **Plagiarism Score:** `{plag_score}%`\n"
                f"- **Originality Score:** `{orig_score}%`\n"
                f"- **Flagged Sentences:** `{matched_sents}` out of `{total_sents}` sentences analyzed.\n\n"
                + ("⚠️ *Recommendation:* You have flagged passages that match existing literature. Use the **Rewrite** tool or cite the referenced sources."
                   if plag_score > 15 else "✅ *Great job!* This document demonstrates high originality.")
            )

        if any(w in q for w in ["how original", "originality score", "is this original", "originality"]):
            return (
                f"✨ **Originality Assessment**\n\n"
                f"- **Originality Score:** `{orig_score}%`\n"
                f"- **Plagiarism Detected:** `{plag_score}%`\n\n"
                + (f"Your document is **{orig_score}% original**. `{total_sents - matched_sents}` out of `{total_sents}` sentences are unique."
                   if total_sents > 0 else "Upload or paste a document to compute an originality score.")
            )

        # 2. Highest similarity / Worst match
        if any(w in q for w in ["highest similarity", "worst match", "most copied", "top match", "biggest match"]):
            if not matches:
                return "ℹ️ No plagiarized sentences were flagged in the current document."
            sorted_m = sorted(matches, key=lambda x: x.get("similarity", 0), reverse=True)
            top = sorted_m[0]
            query_sent = top.get("query_sentence", {}).get("text") or top.get("query_text", "")
            matched_sent = top.get("matched_sentence") or top.get("matched_text", "")
            sim_pct = round(top.get("similarity", 0) * 100, 1)
            source_name = top.get("source", top.get("doc_title", "Unknown Source"))
            return (
                f"🚨 **Highest Similarity Match ({sim_pct}%)**\n\n"
                f"- **Your Sentence:** \"_{query_sent}_\"\n"
                f"- **Matched Against:** \"_{matched_sent}_\"\n"
                f"- **Source:** **{source_name}**\n"
                f"- **Match Type:** `{top.get('match_type', 'lexical').upper()}`\n\n"
                f"👉 You can click this sentence in the **Analyze** view to rewrite it immediately."
            )

        # 3. Top Sources
        if any(w in q for w in ["top sources", "sources", "references", "show sources", "where is it from", "citations"]):
            if not sources:
                if matches:
                    src_names = list(set([m.get("source", m.get("doc_title", "Reference")) for m in matches]))
                    return "📚 **Referenced Sources Found:**\n" + "\n".join([f"- **{s}**" for s in src_names[:5]])
                return "ℹ️ No external reference matches found for this document."
            
            resp = ["📚 **Top Reference Sources Detected:**\n"]
            for idx, s in enumerate(sources[:5], 1):
                title = s.get("title", "Unknown Publication")
                author = s.get("author", "N/A")
                m_count = s.get("match_count", 1)
                sim = round(s.get("max_similarity", 0.0) * 100, 1) if s.get("max_similarity") else ""
                sim_str = f" ({sim}% max match)" if sim else ""
                url_str = f" — [View Source]({s['url']})" if s.get("url") else ""
                resp.append(f"{idx}. **{title}** by *{author}*{sim_str} — `{m_count} match(es)`{url_str}")
            return "\n".join(resp)

        # 4. Analytics / Readability / Word count
        if any(w in q for w in ["word count", "how many words", "analytics", "readability", "reading time", "grade level", "stats"]):
            if not doc_text:
                return "ℹ️ Please upload or paste text first to calculate document analytics."
            return (
                f"📈 **Document Analytics & Readability**\n\n"
                f"- **Total Words:** `{word_count:,}`\n"
                f"- **Characters:** `{len(doc_text):,}`\n"
                f"- **Sentences:** `{total_sents}`\n"
                f"- **Flesch Reading Ease:** `{reading_ease}`\n"
                f"- **Grade Level:** `{grade_level}`\n"
                f"- **Estimated Reading Time:** `{metrics.get('reading_time_minutes', round(word_count/200, 1))} min`\n"
                f"- **Unique Words:** `{metrics.get('unique_word_count', len(set(doc_text.lower().split()))):,}`"
            )

        # 5. Summarize / Main arguments
        if any(w in q for w in ["summarize", "summary", "main argument", "key points", "overview", "tldr", "tl;dr"]):
            if not doc_text:
                return "ℹ️ No document content available to summarize. Please upload or paste a document."
            
            # Smart extractive summary
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", doc_text) if len(s.strip()) > 20]
            if not sentences:
                return f"**Summary:** {doc_text[:250]}..."
            
            lead = sentences[0]
            middle = sentences[len(sentences)//2] if len(sentences) > 2 else ""
            conclusion = sentences[-1] if len(sentences) > 1 else ""

            return (
                f"📝 **Document Summary & Key Takeaways**\n\n"
                f"**TL;DR:** {lead}\n\n"
                f"**Key Core Points:**\n"
                f"1. {lead}\n"
                + (f"2. {middle}\n" if middle else "")
                + (f"3. {conclusion}\n" if conclusion and conclusion != lead else "")
                + f"\n**Word Count:** `{word_count}` words | **Originality:** `{orig_score}%`"
            )

        # 6. Claims that need citations
        if any(w in q for w in ["need citation", "needs citation", "uncited", "claim", "find claims"]):
            if not matches:
                return (
                    "🔍 **Citation Review:**\n\n"
                    "No explicit plagiarism matches were found. However, ensure that all empirical data, historical dates, "
                    "and specialized domain claims are backed with author-date citations (e.g. *Smith et al., 2024*)."
                )
            lines = ["🔍 **Claims & Sentences Requiring Attribution:**\n"]
            for m in matches[:4]:
                sent = m.get("query_sentence", {}).get("text") or m.get("query_text", "")
                src = m.get("source", m.get("doc_title", "Reference"))
                lines.append(f"- **Claim:** \"_{sent}_\"\n  ↳ **Requires citation for:** *{src}*")
            return "\n".join(lines)

        # 7. Generate report request
        if any(w in q for w in ["generate report", "download report", "export pdf", "make report", "report"]):
            return (
                "📄 **Lemma Integrity Report**\n\n"
                "You can generate and download the official PDF / HTML report right now:\n"
                "1. Switch to the **Reports** tab in the sidebar.\n"
                "2. Click **Generate Lemma Integrity Report**.\n"
                "3. Your comprehensive report includes full coordinate highlighting, breakdown by match type, and source provenance."
            )

        # If question is general about the document text, return RAG context
        return None

    async def generate_response(self, user_query: str, context: Dict[str, Any]) -> str:
        """
        Generates an assistant response. Checks deterministic answers first,
        then attempts Ollama generative RAG, and falls back to smart extractive RAG.
        """
        # 1. Deterministic direct answers
        direct_answer = self.answer_deterministic(user_query, context)
        if direct_answer:
            return direct_answer

        doc_text = context.get("text", "") or context.get("document_text", "")
        chunks = self._retrieve_relevant_chunks(doc_text, user_query, top_k=3)
        context_block = "\n---\n".join(chunks)

        system_prompt = (
            "You are Lemma AI, an intelligent document analysis and academic originality assistant. "
            "You assist researchers and writers with editing, summarizing, fact-checking, and ensuring research integrity. "
            "Answer clearly using markdown. Refer strictly to the provided document context when answering.\n\n"
            f"DOCUMENT CONTEXT:\n{context_block if context_block else 'No document uploaded yet.'}"
        )

        # 2. Try Ollama if online
        ollama_reply = await self.ollama.generate_response(system_prompt, user_query)
        if ollama_reply:
            return ollama_reply

        # 3. Smart local RAG fallback
        if chunks:
            return (
                f"🤖 **Lemma Document Assistant (Lite Mode)**\n\n"
                f"Based on the most relevant sections of your document:\n\n"
                + "\n\n".join([f"> \"_{c[:280]}..._\"" for c in chunks[:2]])
                + f"\n\n**Response to '{user_query}':**\n"
                f"The document discusses these concepts in detail. You can use the **Paraphraser** in the sidebar to rephrase specific sections or the **Analyze** tab to review all match coordinates."
            )

        return (
            "🤖 **Lemma Assistant:**\n\n"
            "I am ready to help you analyze your document! You can ask me:\n"
            "- *'What is my plagiarism score?'*\n"
            "- *'Show top 5 sources'*;\n"
            "- *'Which sentence has the highest similarity?'*\n"
            "- *'Summarize this document'*;\n"
            "- *'Find claims that need citations'*; or\n"
            "- *'Document analytics and readability'*."
        )

    async def stream_response(self, user_query: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Streams response tokens for a dynamic, responsive UI.
        """
        # Check if deterministic answer matches
        direct = self.answer_deterministic(user_query, context)
        if direct:
            # Stream words with small delays for organic feel
            words = direct.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + " "
                yield chunk
                await asyncio.sleep(0.015)
            return

        doc_text = context.get("text", "") or context.get("document_text", "")
        chunks = self._retrieve_relevant_chunks(doc_text, user_query, top_k=3)
        context_block = "\n---\n".join(chunks)

        system_prompt = (
            "You are Lemma AI, an intelligent document analysis and academic originality assistant. "
            "Answer clearly using markdown. Refer strictly to the provided document context.\n\n"
            f"DOCUMENT CONTEXT:\n{context_block if context_block else 'No document uploaded yet.'}"
        )

        if await self.ollama.is_available():
            async for token in self.ollama.stream_response(system_prompt, user_query):
                yield token
        else:
            fallback = await self.generate_response(user_query, context)
            words = fallback.split(" ")
            for i in range(0, len(words), 4):
                chunk = " ".join(words[i:i+4]) + " "
                yield chunk
                await asyncio.sleep(0.02)
