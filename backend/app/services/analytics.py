import math
import re

class DocumentAnalyticsService:
    """
    Service for calculating readability scores, word metrics, 
    and document statistics for analyzed academic texts.
    """
    
    @staticmethod
    def analyze_readability(text: str, sentence_count: int = 0) -> dict:
        """
        Computes readability metrics and document stats.
        
        Metrics returned:
        - word_count: Total words
        - char_count: Total characters
        - avg_sentence_length: Words per sentence
        - avg_word_length: Average characters per word
        - flesch_reading_ease: Score (0-100)
        - readability_level: Human readable grade tier
        - reading_time_seconds: Estimated reading duration
        """
        if not text or not text.strip():
            return {
                "word_count": 0,
                "char_count": 0,
                "avg_sentence_length": 0.0,
                "avg_word_length": 0.0,
                "flesch_reading_ease": 100.0,
                "readability_level": "N/A",
                "reading_time_seconds": 0
            }

        # Extract words using regex
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        char_count = len(text)
        
        if sentence_count <= 0:
            sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
            sentence_count = max(len(sentences), 1)

        avg_sentence_length = round(word_count / max(sentence_count, 1), 2)
        
        # Calculate total syllables roughly
        def count_syllables(word: str) -> int:
            w = word.lower()
            if len(w) <= 3:
                return 1
            w = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', w)
            w = re.sub(r'^y', '', w)
            syllables = len(re.findall(r'[aeiouy]{1,2}', w))
            return max(syllables, 1)

        total_syllables = sum(count_syllables(w) for w in words) if words else 0
        avg_syllables_per_word = (total_syllables / word_count) if word_count > 0 else 1.0
        avg_word_length = round(sum(len(w) for w in words) / word_count, 2) if word_count > 0 else 0.0

        # Flesch Reading Ease Formula: 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch_score = max(0.0, min(100.0, round(flesch_score, 1)))

        if flesch_score >= 90:
            level = "Very Easy (5th Grade)"
        elif flesch_score >= 80:
            level = "Easy (6th Grade)"
        elif flesch_score >= 70:
            level = "Fairly Easy (7th Grade)"
        elif flesch_score >= 60:
            level = "Standard (8th-9th Grade)"
        elif flesch_score >= 50:
            level = "Fairly Difficult (10th-12th Grade)"
        elif flesch_score >= 30:
            level = "Difficult (College)"
        else:
            level = "Very Difficult (Postgraduate)"

        # Average reading speed: ~200 words per minute
        reading_time_seconds = math.ceil((word_count / 200.0) * 60)

        return {
            "word_count": word_count,
            "char_count": char_count,
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "flesch_reading_ease": flesch_score,
            "readability_level": level,
            "reading_time_seconds": reading_time_seconds
        }
