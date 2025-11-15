"""
Class to extract and transform book titles from multiple API sources.
"""

import re
from typing import Optional, Dict, List, Tuple, Any
from difflib import SequenceMatcher
from logging import Logger

from config import Config


class BookTransformer:
    """
    Clean and standardize book data for warehouse loading.
    """

    @staticmethod
    def _clean_title(title: Optional[str]) -> Optional[str]:
        """
        Clean a single title string.

        Steps:
        1. Handle nulls / empties
        2. Normalize whitespace (including tabs, newlines)
        3. Remove common edition/format suffixes
        4. Smart case normalization
        5. Clean punctuation artifacts
        """
        if not title or not isinstance(title, str):
            return None

        # 1. Basic whitespace cleanup
        cleaned = " ".join(title.strip().split())
        if not cleaned:
            return None

        # 2. Remove common edition/format suffixes that differ between APIs
        # e.g., "(Hardcover)", "[Kindle Edition]", "(Revised)", etc.
        edition_patterns = [
            r"\s*[\(\[]?(Hardcover|Paperback|Kindle|E-?book|Audio)[\)\]]?\s*$",
            r"\s*[\(\[]?(First|Second|Third|\d+(?:st|nd|rd|th)) Edition[\)\]]?\s*$",
            r"\s*[\(\[](Revised|Annotated|Illustrated|Unabridged)[\)\]]\s*$",
            r"\s*-\s*(Revised|Annotated|Illustrated)\s*$",
        ]
        for pattern in edition_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

        # 3. Smart case normalization (only if ALL CAPS or all lowercase)
        if cleaned.isupper() or cleaned.islower():
            cleaned = cleaned.title()

        # 4. Normalize multiple spaces again after removals
        cleaned = " ".join(cleaned.split())

        # 5. Remove trailing/leading punctuation artifacts
        cleaned = cleaned.strip(".,;:-_")

        return cleaned if cleaned else None

    @staticmethod
    def _similarity_score(str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings (0.0 to 1.0)."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    @staticmethod
    def _merge_titles(
        gb_title: Optional[str], ol_title: Optional[str]
    ) -> Tuple[Optional[str], bool]:
        """
        Merge titles from Google Books and Open Library with conflict resolution.

        Priority logic:
        1. If only one source has a title, use it
        2. If both match after cleaning, use either (prefer GB for consistency)
        3. If similar (>90% match), prefer the longer one (likely has subtitle)
        4. If significantly different (<90% match), prefer Google Books
           (typically more complete metadata)

        Args:
            gb_title: Title from Google Books API
            ol_title: Title from Open Library API

        Returns:
            Tuple of (merged_title, title_has_conflict)
        """
        title_has_conflict = False

        if not gb_title and not ol_title:
            return None, title_has_conflict

        if not gb_title:
            return ol_title, title_has_conflict

        if not ol_title:
            return gb_title, title_has_conflict

        # Both exist - check similarity
        similarity = BookTransformer._similarity_score(gb_title, ol_title)

        # If very similar (>90%), prefer the longer one (likely includes subtitle)
        if similarity >= 0.9:
            preferred = gb_title if len(gb_title) >= len(ol_title) else ol_title
            return preferred, title_has_conflict

        # If different, prefer Google Books (typically more reliable)
        title_has_conflict = True
        return gb_title, title_has_conflict

    @staticmethod
    def _normalize_language_code(code: Optional[str]) -> Optional[str]:
        """
        Normalize language codes to ISO 639-1 (2-letter) format.

        Handles:
        - ISO 639-2/T (3-letter): "eng" -> "en"
        - Already 2-letter: "en" -> "en"
        - Common variations

        Args:
            code: Language code string (2 or 3 letters)

        Returns:
            Normalized 2-letter ISO 639-1 code or None
        """
        if not code or not isinstance(code, str):
            return None

        code = code.strip().lower()

        # Map 3-letter to 2-letter codes (ISO 639-2 to ISO 639-1)
        # If it's 3 letters, try to convert
        if len(code) == 3:
            return Config.LANGUAGE_CODE_MAP.get(code, code)

        # If it's 2 letters, assume it's already correct
        if len(code) == 2:
            return code

        return None

    @staticmethod
    def _merge_languages(
        gb_language: Optional[str],
        ol_languages: Optional[list],
        logger: Optional[Logger] = None,
    ) -> Optional[List[str]]:
        """
        Merge language data from both sources intelligently.

        Logic:
        1. Start with OL's language array (work-level data)
        2. Add GB's edition language if not already in the list
        3. Normalize all codes to 2-letter format
        4. Remove duplicates and sort

        This handles cases where:
        - GB has a language that OL doesn't (adds it)
        - OL has languages GB doesn't (keeps them)
        - Both sources have overlapping languages (deduplicates)

        Args:
            gb_language: Single language from Google Books (e.g., "en", "es")
            ol_languages: Array from Open Library (e.g., ["eng", "fre", "spa"])
            logger: Optional logger for data quality warnings

        Returns:
            Merged and normalized language list (e.g., ["en", "es", "fr"])
            or None if no valid languages found
        """
        languages = set()  # Use set to avoid duplicates

        # 1. Add Open Library languages (work-level: all translations)
        if ol_languages and isinstance(ol_languages, list):
            for lang in ol_languages:
                normalized = BookTransformer._normalize_language_code(lang)
                if normalized:
                    languages.add(normalized)

        # 2. Add Google Books language (edition-level: THIS ISBN's language)
        gb_normalized = None
        if gb_language:
            gb_normalized = BookTransformer._normalize_language_code(gb_language)
            if gb_normalized:
                languages.add(gb_normalized)

        # 4. Convert to sorted list for consistent ordering
        if languages:
            return sorted(list(languages))

        return None

    @staticmethod
    def transform_book(
        gb_book_info: Dict,
        gb_info: Dict,
        ol_info: Dict,
    ) -> Optional[Dict]:
        """
        Transform book attributes from both API sources.

        Args:
            gb_book_info: Google Books volumeInfo dict
            gb_info: Full Google Books response
            ol_info: Open Library docs[0] dict

        Returns:
            Dict with cleaned book attributes for dim_books table
        """
        # ! working with titles
        # Extract raw titles
        gb_title = gb_book_info.get("title")
        ol_title = ol_info.get("title")

        # Clean both titles
        gb_cleaned = BookTransformer._clean_title(gb_title)
        ol_cleaned = BookTransformer._clean_title(ol_title)

        # Merge with conflict resolution
        cleaned_title, title_has_conflict = BookTransformer._merge_titles(
            gb_cleaned, ol_cleaned
        )

        # Language handling - merge both sources
        gb_language = gb_book_info.get("language")
        ol_languages = ol_info.get("language")

        merged_languages = BookTransformer._merge_languages(gb_language, ol_languages)

        return {
            "title": cleaned_title if cleaned_title else "",
            "title_has_conflict": title_has_conflict,
            "description": gb_book_info.get("description", ""),
            "language": merged_languages,
            "page_count": gb_book_info.get("pageCount")
            or None,  # Use None instead of 0 to satisfy DB constraint
            "cover_image_id": gb_book_info.get("imageLinks", {}).get("thumbnail", ""),
            "work_key": "",  # this is not needed for now
        }

    @staticmethod
    def transform_book_metrics(
        google_books_data: Optional[Dict[str, Any]],
        open_library_data: Optional[Dict[str, Any]],
    ) -> Dict:
        """
        Transform book metrics data from both APIs.

        Google Books provides: rating_avg, rating_count, list_price_amount,
                             retail_price_amount, currency_code, is_ebook_available,
                             saleability_status
        Open Library provides: edition_count

        Args:
            book_isbn: ISBN of the book
            google_books_data: Raw Google Books API response (full response with items array)
            open_library_data: Raw Open Library API response (full response with docs array)

        Returns:
            Dict with all fact_book_metrics fields ready for database insertion
        """
        # Extract nested data from Google Books
        gb_items = google_books_data.get("items", []) if google_books_data else []
        if not gb_items:
            gb_volume_info = {}
            gb_sale_info = {}
        else:
            gb_item = gb_items[0]
            gb_volume_info = gb_item.get("volumeInfo", {})
            gb_sale_info = gb_item.get("saleInfo", {})

        # Extract edition count from Open Library
        ol_docs = open_library_data.get("docs", []) if open_library_data else []
        ol_edition_count = ol_docs[0].get("edition_count") if ol_docs else None

        # Extract pricing info
        list_price = gb_sale_info.get("listPrice", {})
        retail_price = gb_sale_info.get("retailPrice", {})

        return {
            "rating_avg": gb_volume_info.get("averageRating"),
            "rating_count": gb_volume_info.get("ratingsCount"),
            "edition_count": ol_edition_count,
            "list_price_amount": list_price.get("amount"),
            "retail_price_amount": retail_price.get("amount"),
            "currency_code": list_price.get("currencyCode")
            or retail_price.get("currencyCode"),
            "is_ebook_available": gb_sale_info.get("isEbook", False),
            "saleability_status": gb_sale_info.get("saleability"),
        }
