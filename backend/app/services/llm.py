import httpx
import logging
import re
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service to interact with the local Ollama LLM for text rewriting."""

    @classmethod
    def fallback_rewrite_text(cls, text: str, tone: str = "academic") -> str:
        """Provide a lightweight local fallback when Ollama is unavailable."""
        cleaned = (text or "").strip()
        if not cleaned:
            return ""

        tone_prefixes = {
            "academic": "In academic terms, ",
            "standard": "In clearer language, ",
            "creative": "A more polished version reads: ",
        }

        replacements = {
            "important": "significant",
            "good": "effective",
            "bad": "detrimental",
            "use": "utilize",
            "shows": "demonstrates",
            "needs": "requires",
            "problem": "challenge",
            "idea": "concept",
            "big": "substantial",
            "help": "support",
            "think": "consider",
            "change": "transform",
            "strong": "robust",
            "quick": "rapid",
            "fast": "expeditious",
            "find": "identify",
            "make": "create",
            "look": "examine",
            "very": "highly",
            "people": "individuals",
            "work": "operate",
            "start": "commence",
            "get": "obtain",
        }

        rewritten = cleaned
        for old, new in replacements.items():
            pattern = r"\b" + re.escape(old) + r"\b"
            rewritten = re.sub(pattern, new, rewritten, flags=re.IGNORECASE)

        sentences = re.split(r"(?<=[.!?])\s+", rewritten)
        transformed = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if tone in tone_prefixes and not re.match(r"^(In |A |This |It )", sentence, flags=re.IGNORECASE):
                sentence = sentence[0].upper() + sentence[1:]
                sentence = f"{tone_prefixes[tone]}{sentence}"
            transformed.append(sentence)

        final = " ".join(transformed)
        if final == cleaned:
            final = f"{tone_prefixes.get(tone, 'In clearer terms, ')}{cleaned[0].upper()}{cleaned[1:]}"
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
                else:
                    logger.warning(f"Ollama tags endpoint returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to fetch models from Ollama: {e}")
        return []

    @classmethod
    async def rewrite_text(cls, text: str, tone: str = "academic") -> str:
        """
        Rewrites a sentence or paragraph to eliminate plagiarism,
        maintaining a specified tone.
        """
        if not text.strip():
            return ""

        # Fetch available models
        available = await cls.get_available_models()
        model_to_use = settings.OLLAMA_MODEL
        
        # Determine model to use
        if available:
            if model_to_use not in available:
                # Try prefix matching (e.g., matching "llama3" to "llama3:latest")
                candidates = [
                    m for m in available 
                    if m.startswith(model_to_use) or model_to_use.startswith(m.split(':')[0])
                ]
                if candidates:
                    model_to_use = candidates[0]
                    logger.info(f"Requested model '{settings.OLLAMA_MODEL}' not found. Using matched model '{model_to_use}'.")
                else:
                    model_to_use = available[0]
                    logger.info(f"Requested model '{settings.OLLAMA_MODEL}' not found. Falling back to first available model '{model_to_use}'.")
        else:
            logger.warning("No models found in Ollama tags query. Attempting call with default model configuration.")

        # Determine prompt instructions and generation options based on tone
        tone_instruction = "Maintain a strict academic and professional tone."
        temp = 0.5
        presence_penalty = 1.0
        frequency_penalty = 1.0
        
        if tone == "creative":
            tone_instruction = "Use a creative, engaging, and modern tone."
            temp = 0.85
            presence_penalty = 1.2
            frequency_penalty = 1.2
        elif tone == "standard":
            tone_instruction = "Use a clear, neutral, and highly readable tone."
            temp = 0.7
            presence_penalty = 1.1
            frequency_penalty = 1.1

        # Construct generation prompt
        prompt = (
            "You are an expert academic and technical editor. Rewrite the following sentence or text segment to eliminate plagiarism. "
            f"{tone_instruction} Preserve the original meaning, and ensure it is grammatically correct. "
            "Respond ONLY with the rewritten text, and do not include any introductory remarks, quotes, markdown formatting, explanations, or filler text.\n\n"
            f"Original text: {text}\n\n"
            "Rewritten text:"
        )
        
        payload = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "top_p": 0.9,
                "top_k": 40
            }
        }
        
        url = f"{settings.OLLAMA_URL.rstrip('/')}/api/generate"
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    rewritten = data.get("response", "").strip()
                    
                    # Clean up any surrounding quotes that the LLM might have outputted
                    if rewritten.startswith('"') and rewritten.endswith('"'):
                        rewritten = rewritten[1:-1].strip()
                    elif rewritten.startswith("'") and rewritten.endswith("'"):
                        rewritten = rewritten[1:-1].strip()
                    return rewritten
                else:
                    logger.error(f"Ollama returned error status: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Ollama service error: Received status {response.status_code}."
                    )
        except (httpx.RequestError, HTTPException, OSError) as e:
            logger.warning(f"Ollama unavailable at {settings.OLLAMA_URL}. Falling back to local rewrite: {e}")
            return cls.fallback_rewrite_text(text, tone=tone)
