# backend/app/services/ingestion/language_detection.py

from langdetect import detect, DetectorFactory, LangDetectException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Ensure deterministic results
DetectorFactory.seed = 42


class LanguageDetector:
    """
    Centralized language detection utility.

    Used during:
    - Document ingestion
    - Query processing
    - Metadata enrichment

    Keeps language detection consistent across the system.
    """

    def __init__(self, default_language: str | None = None):
        self.default_language = default_language or settings.DEFAULT_LANGUAGE

    def detect_language(self, text: str) -> str:
        """
        Detect language for a given text.

        Falls back to DEFAULT_LANGUAGE on failure.
        """
        if not text or not text.strip():
            logger.warning("Empty text received for language detection")
            return self.default_language

        try:
            language = detect(text)
            return language
        except LangDetectException as e:
            logger.warning(
                f"Language detection failed, falling back to "
                f"{self.default_language}: {e}"
            )
            return self.default_language
        except Exception as e:
            logger.error(
                f"Unexpected error during language detection, "
                f"falling back to {self.default_language}: {e}"
            )
            return self.default_language
