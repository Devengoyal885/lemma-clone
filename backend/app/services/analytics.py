import math
import re

class DocumentAnalyticsService:
    """
    Service for calculating readability scores, word metrics, 
    lexical diversity, and document statistics for analyzed texts.
    """
    
    @staticmethod
    def analyze_readability(text: str, sentence_count: int = 0) -> dict:
        """
        Computes comprehensive readability metrics and document stats.
        
        Metrics returned:
        - word_count: Total words
        - char_count: Total characters
        - sentence_count: Total sentences
        - paragraph_count: Total paragraphs
        - avg_sentence_length: Words per sentence
        - avg_word_length: Average characters per word
        - unique_word_count: Total distinct words
        - lexical_diversity: Ratio of unique words to total words (0.0 - 1.0)
        - flesch_reading_ease: Score (0-100)
        - flesch_kincaid_grade: US School Grade Level
        - readability_level: Human readable grade tier
        - reading_time_seconds: Estimated reading duration in seconds
        - reading_time_minutes: Estimated reading duration in minutes
        """
        if not text or not text.strip():
            return {
                "word_count": 0,
                "char_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "avg_sentence_length": 0.0,
                "avg_word_length": 0.0,
                "unique_word_count": 0,
                "lexical_diversity": 0.0,
                "flesch_reading_ease": 100.0,
                "flesch_kincaid_grade": "0.0",
                "readability_level": "N/A",
                "reading_time_seconds": 0,
                "reading_time_minutes": 0.0
            }

        # Extract words using regex
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        char_count = len(text)
        
        # Paragraphs
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\r\n\r\n', text) if p.strip()]
        paragraph_count = max(1, len(paragraphs))

        if sentence_count <= 0:
            sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
            sentence_count = max(len(sentences), 1)

        avg_sentence_length = round(word_count / max(sentence_count, 1), 2)
        
        # Unique words & Lexical Diversity
        unique_words = set(w.lower() for w in words)
        unique_word_count = len(unique_words)
        lexical_diversity = round((unique_word_count / word_count), 3) if word_count > 0 else 0.0

        # Calculate total syllables
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

        # Flesch-Kincaid Grade Level: 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
        fk_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        fk_grade = max(0.0, round(fk_grade, 1))

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
        reading_time_minutes = round(word_count / 200.0, 1)

        return {
            "word_count": word_count,
            "char_count": char_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "unique_word_count": unique_word_count,
            "lexical_diversity": lexical_diversity,
            "flesch_reading_ease": flesch_score,
            "flesch_kincaid_grade": f"{fk_grade}",
            "readability_level": level,
            "reading_time_seconds": reading_time_seconds,
            "reading_time_minutes": reading_time_minutes
        }
