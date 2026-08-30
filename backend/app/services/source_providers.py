"""
Source Discovery Providers for Lemma
Fetches public academic, open-access, and encyclopedia references without scraping Google.
Providers:
- WikipediaProvider
- OpenAlexProvider
- CrossrefProvider
- ArxivProvider
- LocalCorpusProvider (offline fallback)
"""

import logging
import asyncio
import httpx
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class SourceProvider(ABC):
    """Abstract base class for academic / public source providers."""

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search the external repository and return normalized results."""
        pass


class WikipediaProvider(SourceProvider):
    """Fetches overview articles and references from Wikipedia API."""

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": limit,
            "utf8": 1
        }
        headers = {"User-Agent": "LemmaOriginalityEngine/2.0 (academic research platform)"}

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    search_results = data.get("query", {}).get("search", [])
                    results = []
                    for item in search_results:
                        page_id = item.get("pageid")
                        title = item.get("title", "")
                        snippet = item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                        page_url = f"https://en.wikipedia.org/?curid={page_id}"
                        results.append({
                            "id": f"wiki_{page_id}",
                            "title": title,
                            "author": "Wikipedia Contributors",
                            "source": "Wikipedia, The Free Encyclopedia",
                            "url": page_url,
                            "category": "General Reference",
                            "text": snippet,
                            "provider": "Wikipedia"
                        })
                    return results
        except Exception as e:
            logger.debug(f"WikipediaProvider error: {e}")
        return []


class OpenAlexProvider(SourceProvider):
    """Fetches open science academic works from OpenAlex API."""

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        url = "https://api.openalex.org/works"
        params = {
            "search": query,
            "per-page": limit,
            "mailto": "research@lemma.local"
        }

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for work in data.get("results", []):
                        work_id = work.get("id", "").split("/")[-1]
                        title = work.get("title") or "Untitled Academic Work"
                        
                        # Authors
                        authorships = work.get("authorships", [])
                        authors = [a.get("author", {}).get("display_name", "") for a in authorships if a.get("author")]
                        author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "Unknown"
                        
                        # Venue / Year
                        host_venue = work.get("primary_location", {}).get("source", {}).get("display_name") or "Open Access Repository"
                        pub_year = work.get("publication_year") or "N/A"
                        source_str = f"{host_venue} ({pub_year})"
                        
                        doi_url = work.get("doi") or work.get("id") or ""
                        
                        # Abstract inversion if available
                        abstract = ""
                        inv_index = work.get("abstract_inverted_index")
                        if inv_index:
                            word_positions = []
                            for word, positions in inv_index.items():
                                for pos in positions:
                                    word_positions.append((pos, word))
                            word_positions.sort(key=lambda x: x[0])
                            abstract = " ".join([w[1] for w in word_positions[:80]])

                        results.append({
                            "id": f"openalex_{work_id}",
                            "title": title,
                            "author": author_str,
                            "source": source_str,
                            "url": doi_url,
                            "category": "Academic",
                            "text": abstract or title,
                            "provider": "OpenAlex"
                        })
                    return results
        except Exception as e:
            logger.debug(f"OpenAlexProvider error: {e}")
        return []


class CrossrefProvider(SourceProvider):
    """Fetches peer-reviewed publications and DOIs from Crossref API."""

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "rows": limit
        }
        headers = {"User-Agent": "LemmaOriginalityEngine/2.0 (mailto:dev@lemma.local)"}

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("message", {}).get("items", [])
                    results = []
                    for item in items:
                        title_list = item.get("title", [])
                        title = title_list[0] if title_list else "Crossref Document"
                        
                        authors = []
                        for a in item.get("author", []):
                            given = a.get("given", "")
                            family = a.get("family", "")
                            authors.append(f"{given} {family}".strip())
                        author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "Unknown"

                        container = item.get("container-title", [])
                        container_str = container[0] if container else "Scholarly Publisher"
                        doi = item.get("DOI", "")
                        url_str = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")

                        results.append({
                            "id": f"crossref_{doi.replace('/', '_') if doi else title[:15]}",
                            "title": title,
                            "author": author_str,
                            "source": container_str,
                            "url": url_str,
                            "category": "Academic",
                            "text": item.get("abstract", "") or title,
                            "provider": "Crossref"
                        })
                    return results
        except Exception as e:
            logger.debug(f"CrossrefProvider error: {e}")
        return []


class ArxivProvider(SourceProvider):
    """Fetches academic preprints from arXiv API."""

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": f'all:"{query}"',
            "max_results": limit
        }

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    root = ET.fromstring(resp.content)
                    entries = root.findall('atom:entry', ns)
                    
                    candidates = []
                    for entry in entries:
                        title_elem = entry.find('atom:title', ns)
                        summary_elem = entry.find('atom:summary', ns)
                        id_elem = entry.find('atom:id', ns)
                        
                        if title_elem is None or id_elem is None:
                            continue
                            
                        title = title_elem.text.strip().replace("\n", " ")
                        abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""
                        paper_url = id_elem.text.strip()
                        paper_id = paper_url.split('/abs/')[-1].split('v')[0]
                        
                        authors = [
                            auth.find('atom:name', ns).text.strip() 
                            for auth in entry.findall('atom:author', ns) 
                            if auth.find('atom:name', ns) is not None
                        ]
                        author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "N/A"
                        
                        candidates.append({
                            "id": f"arxiv_{paper_id}",
                            "title": title,
                            "author": author_str,
                            "source": f"arXiv Preprint",
                            "url": paper_url,
                            "category": "Technology & Science",
                            "text": abstract,
                            "provider": "arXiv"
                        })
                    return candidates
        except Exception as e:
            logger.debug(f"ArxivProvider error: {e}")
        return []


class LocalCorpusProvider(SourceProvider):
    """Provides categorized references from the local reference database."""

    def __init__(self):
        from app.services.lite_matcher import LiteMatcher
        self.matcher = LiteMatcher()

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        results = []
        q_lower = (query or "").lower().strip()
        
        for doc in self.matcher.references:
            title = doc.get("title", "")
            author = doc.get("author", "")
            text = doc.get("text", "") or doc.get("content", "")
            cat = doc.get("category", "General")
            
            # Simple keyword match or relevance
            score = 0
            if q_lower in title.lower():
                score += 3
            if q_lower in text.lower():
                score += 1
            if q_lower in cat.lower():
                score += 1

            if score > 0 or not q_lower:
                results.append({
                    "id": doc.get("id", ""),
                    "title": title,
                    "author": author,
                    "source": doc.get("source", "Reference Library"),
                    "url": doc.get("url", ""),
                    "category": cat,
                    "text": text[:300] + ("..." if len(text) > 300 else ""),
                    "provider": "Local Reference Corpus"
                })

        return results[:limit]


class SourceDiscoveryService:
    """Orchestrates multi-provider academic discovery with automatic fallback."""

    def __init__(self):
        self.providers: Dict[str, SourceProvider] = {
            "wikipedia": WikipediaProvider(),
            "openalex": OpenAlexProvider(),
            "crossref": CrossrefProvider(),
            "arxiv": ArxivProvider(),
        }
        self.local_provider = LocalCorpusProvider()

    async def discover(self, query: str, provider_names: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
        """Query selected providers or all providers in parallel."""
        selected_providers = []
        if provider_names:
            for p in provider_names:
                if p.lower() in self.providers:
                    selected_providers.append(self.providers[p.lower()])
        else:
            selected_providers = list(self.providers.values())

        tasks = [p.search(query, limit=5) for p in selected_providers]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        merged_results = []
        seen_titles = set()

        for res in gathered:
            if isinstance(res, list):
                for item in res:
                    title_norm = item.get("title", "").strip().lower()
                    if title_norm and title_norm not in seen_titles:
                        seen_titles.add(title_norm)
                        merged_results.append(item)

        # Fallback to local corpus if no results or external failure
        if not merged_results:
            local_res = await self.local_provider.search(query, limit=limit)
            merged_results.extend(local_res)

        return {
            "query": query,
            "total_results": len(merged_results),
            "sources": merged_results[:limit]
        }
