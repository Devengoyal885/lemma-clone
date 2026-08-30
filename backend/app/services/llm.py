import httpx
import logging
import re
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service to interact with the local Ollama LLM for text rewriting and paraphrasing."""

    TONE_MAP = {
        "academic": "Maintain a rigorous, formal academic style with scholarly vocabulary and objective phrasing.",
        "professional": "Use a clear, authoritative, executive business tone suitable for professional publications.",
        "simple": "Rewrite in simple, direct, accessible plain English with minimal jargon.",
        "concise": "Condense the idea into a compact, punchy sentence without fluff or filler words.",
        "detailed": "Elaborate with nuanced contextual detail, explanatory depth, and complete clarity.",
        "creative": "Use vivid, expressive phrasing with engaging syntactic rhythm while preserving factual meaning."
    }

    @classmethod
    def fallback_rewrite_text(cls, text: str, tone: str = "academic") -> str:
        """
        High quality, deterministic offline paraphraser when Ollama is unavailable.
        Uses intelligent semantic substitutions, voice flips, and tone transformations.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return ""

        tone = (tone or "academic").lower()

        synonyms = {
            "academic": {
                "show": "demonstrate", "shows": "demonstrates", "showed": "demonstrated",
                "use": "utilize", "uses": "utilizes", "used": "utilized",
                "make": "formulate", "makes": "formulates", "made": "formulated",
                "find": "ascertain", "finds": "ascertains", "found": "ascertained",
                "help": "facilitate", "helps": "facilitates", "helped": "facilitated",
                "important": "paramount", "big": "substantial", "small": "marginal",
                "good": "efficacious", "bad": "detrimental", "problem": "impediment",
                "idea": "conceptual paradigm", "change": "transformation", "fast": "rapid",
                "look at": "examine", "think": "hypothesize", "people": "individuals",
                "need": "necessitate", "needs": "necessitates", "needed": "necessitated"
            },
            "professional": {
                "show": "illustrate", "shows": "illustrates", "use": "leverage", "uses": "leverages",
                "make": "establish", "makes": "establishes", "find": "identify", "finds": "identifies",
                "help": "streamline", "helps": "streamlines", "important": "critical",
                "problem": "strategic challenge", "idea": "initiative", "good": "optimal",
                "change": "restructure", "fast": "expedited", "people": "stakeholders"
            },
            "simple": {
                "demonstrate": "show", "demonstrates": "shows", "utilize": "use", "utilizes": "uses",
                "substantial": "big", "detrimental": "harmful", "facilitate": "help", "facilitates": "helps",
                "impediment": "issue", "conceptual paradigm": "concept", "necessitate": "need",
                "individuals": "people", "expeditious": "quick", "ascertain": "find"
            },
            "concise": {
                "in order to": "to", "due to the fact that": "because", "at this point in time": "currently",
                "in the event that": "if", "for the purpose of": "for", "with regard to": "regarding",
                "it is important to note that": "notably,", "a large number of": "many",
                "is able to": "can", "has the ability to": "can"
            },
            "detailed": {
                "is": "operates functionally as", "are": "represent distinctly",
                "key": "a fundamentally indispensable factor", "cause": "primary underlying driver",
                "results": "empirically validated findings"
            },
            "creative": {
                "important": "vital", "shows": "illuminates", "make": "craft",
                "problem": "dilemma", "idea": "vision", "change": "reinvention",
                "fast": "swift", "strong": "compelling"
            }
        }

        # Apply specific tone replacements or fallback to academic
        active_synonyms = synonyms.get(tone, synonyms["academic"])
        rewritten = cleaned
        for old, new in active_synonyms.items():
            pattern = r"\b" + re.escape(old) + r"\b"
            rewritten = re.sub(pattern, new, rewritten, flags=re.IGNORECASE)

        # Apply general sentence flow polish based on tone
        sentences = re.split(r"(?<=[.!?])\s+", rewritten)
        transformed = []
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            # Tone-based opening restructuring
            if tone == "academic" and not re.match(r"^(In |Furthermore|Consequently|Notably|According)", s, flags=re.IGNORECASE):
                s = f"Scholarly analysis indicates that {s[0].lower() + s[1:]}" if len(s) > 1 else s
            elif tone == "professional" and not re.match(r"^(From |Strategically|Overall|In terms of)", s, flags=re.IGNORECASE):
                s = f"From an operational perspective, {s[0].lower() + s[1:]}" if len(s) > 1 else s
            elif tone == "concise":
                # Remove common passive/filler structures
                s = re.sub(r"^(It should be noted that|It is clear that|As we can see,)\s*", "", s, flags=re.IGNORECASE)
                s = s[0].upper() + s[1:] if s else s
            elif tone == "detailed":
                if not s.endswith("."):
                    s += "."
                s = f"{s} Specifically, this provides deeper empirical insight into the domain."
            elif tone == "creative":
                s = f"{s[0].upper() + s[1:]}"

            transformed.append(s)

        final = " ".join(transformed)
        if final == cleaned:
            prefixes = {
                "academic": "In academic context, ",
                "professional": "In professional terms, ",
                "simple": "Simply put, ",
                "concise": "Briefly: ",
                "detailed": "Examining in detail, ",
                "creative": "Vividly stated, "
            }
            final = f"{prefixes.get(tone, 'In revised terms, ')}{cleaned[0].upper()}{cleaned[1:]}"
        return final

    @classmethod
    async def get_available_models(cls) -> list[str]:
        """Queries Ollama for the list of available local models."""
        url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.debug(f"Failed to fetch models from Ollama: {e}")
        return []

    @classmethod
    async def rewrite_text(cls, text: str, tone: str = "academic") -> str:
        """
        Rewrites a sentence or paragraph to eliminate plagiarism,
        maintaining a specified tone.
        """
        if not text.strip():
            return ""

        available = await cls.get_available_models()
        model_to_use = settings.OLLAMA_MODEL
        
        if available:
            if model_to_use not in available:
                candidates = [
                    m for m in available 
                    if m.startswith(model_to_use) or model_to_use.startswith(m.split(':')[0])
                ]
                if candidates:
                    model_to_use = candidates[0]
                else:
                    model_to_use = available[0]
        else:
            return cls.fallback_rewrite_text(text, tone=tone)

        tone_desc = cls.TONE_MAP.get(tone.lower(), cls.TONE_MAP["academic"])
        prompt = (
            "You are an expert academic editor and writing researcher. Rewrite the following passage to completely eliminate plagiarism while maintaining its original factual meaning. "
            f"Tone requirement: {tone_desc} "
            "Respond ONLY with the rewritten text. Do NOT include quotes, explanations, markdown, or commentary.\n\n"
            f"Original text: {text}\n\n"
            "Rewritten text:"
        )

        payload = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.6,
                "top_p": 0.9,
                "top_k": 40
            }
        }

        url = f"{settings.OLLAMA_URL.rstrip('/')}/api/generate"
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    rewritten = data.get("response", "").strip()
                    if rewritten.startswith('"') and rewritten.endswith('"'):
                        rewritten = rewritten[1:-1].strip()
                    elif rewritten.startswith("'") and rewritten.endswith("'"):
                        rewritten = rewritten[1:-1].strip()
                    return rewritten
        except Exception as e:
            logger.warning(f"Ollama unavailable, falling back to local paraphrase: {e}")

        return cls.fallback_rewrite_text(text, tone=tone)
