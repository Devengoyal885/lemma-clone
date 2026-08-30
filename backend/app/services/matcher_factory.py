"""
Matcher Factory - Selects between Lite and Advanced matchers based on service availability
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MatcherFactory:
    """
    Factory that selects the appropriate matcher (Lite or Advanced) based on service availability.
    """

    _instance = None
    _matcher = None
    _mode = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls):
        """Initialize the matcher based on available services."""
        if cls._matcher is not None:
            return cls._matcher

        mode, matcher = cls._detect_and_initialize()
        cls._mode = mode
        cls._matcher = matcher
        return matcher

    @classmethod
    def _detect_and_initialize(cls):
        """
        Detect available services and initialize appropriate matcher.
        Returns: (mode: str, matcher: object)
        """
        # Try PostgreSQL + Elasticsearch first
        if cls._try_advanced_mode():
            logger.info("Initialized in ADVANCED mode (PostgreSQL + Elasticsearch)")
            return "advanced", cls._create_advanced_matcher()

        # Fall back to Lite Mode
        logger.info("Initialized in LITE mode (TF-IDF + local references)")
        return "lite", cls._create_lite_matcher()

    @classmethod
    def _try_advanced_mode(cls) -> bool:
        """Check if PostgreSQL and Elasticsearch are available."""
        try:
            from app.services.database import DatabaseService
            # Try to connect to PostgreSQL
            conn = DatabaseService.get_connection()
            conn.close()
            logger.debug("PostgreSQL connection successful")
            return True
        except Exception as e:
            logger.debug(f"PostgreSQL unavailable: {e}")
            return False

    @classmethod
    def _create_advanced_matcher(cls):
        """Create an advanced matcher instance."""
        from app.services.matcher import DualTierMatcher
        return DualTierMatcher()

    @classmethod
    def _create_lite_matcher(cls):
        """Create a lite matcher instance."""
        from app.services.lite_matcher import LiteMatcher
        return LiteMatcher()

    @classmethod
    def get_matcher(cls):
        """Get the current matcher instance."""
        if cls._matcher is None:
            cls.initialize()
        return cls._matcher

    @classmethod
    def get_mode(cls) -> str:
        """Get the current operation mode (lite or advanced)."""
        if cls._mode is None:
            cls.initialize()
        return cls._mode

    @classmethod
    def get_status(cls) -> dict:
        """Get the current matcher status and mode information."""
        if cls._mode is None:
            cls.initialize()
        
        return {
            "mode": cls._mode,
            "matcher_type": cls._matcher.__class__.__name__ if cls._matcher else "unknown",
        }
