"""
Enhanced AuthorTransformer with multi-source merging capability
"""

import re
import time
from typing import Optional, List, Dict
from difflib import SequenceMatcher


class AuthorTransformer:
    """
    Clean and standardize author data for warehouse loading.

    Args:
        author_name: Author name from Google Books or Open Library
        author_key: Open Library author key (optional, from Open Library API)

    Returns:
        Dict with cleaned author dimension record or None if validation fails

    Cleaning steps:
    1. Handle nulls/empties
    2. Normalize whitespace
    3. Clean special characters
    4. Normalize name capitalization
    5. Validate author key format

    TODO: these are not included in the current cleaning implementation:
    1. Unicode normalization (curly quotes, accented chars, diacritics): "García Márquez", "François"
    2. Names with prefixes/suffixes: "Dr. Seuss", "Mary Shelley, Ph.D."
    3. Inconsistent punctuation in initials: "J R R Tolkien" vs "J.R.R. Tolkien"
    4. Authors with multiple spaces between initials: "J.R.R. Tolkien": "J. R. R. Tolkien"
    5. Non-Latin scripts: "村上 春樹" (Japanese), "Лев Толстой"
    6.


    """

    @staticmethod
    def _normalize_for_comparison(name: str) -> str:
        """
        Normalize author name for fuzzy matching.
        Removes punctuation, extra spaces, converts to lowercase.
        """
        if not name:
            return ""

        # Remove punctuation and normalize
        normalized = re.sub(r"[^\w\s]", "", name.lower())
        normalized = " ".join(normalized.split())
        return normalized

    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        """
        Calculate similarity ratio between two author names (0.0 to 1.0).
        Uses SequenceMatcher for fuzzy matching.
        """
        norm1 = AuthorTransformer._normalize_for_comparison(name1)
        norm2 = AuthorTransformer._normalize_for_comparison(name2)

        if not norm1 or not norm2:
            return 0.0

        return SequenceMatcher(None, norm1, norm2).ratio()

    @staticmethod
    def _find_matching_author(
        target_name: str, candidate_names: List[str], threshold: float = 0.85
    ) -> Optional[int]:
        """
        Find the index of a matching author in candidate list.

        Args:
            target_name: Author name to match
            candidate_names: List of candidate author names
            threshold: Similarity threshold (0.85 = 85% match)

        Returns:
            Index of best match, or None if no match above threshold
        """
        best_match_idx = None
        best_score = threshold

        for idx, candidate in enumerate(candidate_names):
            score = AuthorTransformer._calculate_similarity(target_name, candidate)
            if score > best_score:
                best_score = score
                best_match_idx = idx

        return best_match_idx

    @staticmethod
    def transform_author_attributes(
        author_name: str, author_key: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Clean and standardize author data for warehouse loading.
        (Keep existing implementation)
        """
        # 1. Handle null/empty author name
        if not author_name or not isinstance(author_name, str):
            return None

        # 2. Basic whitespace cleanup
        cleaned_name = " ".join(author_name.strip().split())
        if not cleaned_name:
            return None

        # 3. Remove extra punctuation/unicode artifacts
        cleaned_name = re.sub(r'^["\'\s]+|["\'\s]+$', "", cleaned_name)

        # Fix common unicode issues
        quote_map = {
            "\u201c": '"',
            "\u201d": '"',
            "\u2018": "'",
            "\u2019": "'",
        }
        for fancy, straight in quote_map.items():
            cleaned_name = cleaned_name.replace(fancy, straight)

        # 4. Normalize name capitalization
        if cleaned_name.islower() or cleaned_name.isupper():
            cleaned_name = cleaned_name.title()

        # 5. Clean and validate author key
        cleaned_key = None
        if author_key and isinstance(author_key, str):
            cleaned_key = author_key.strip()
            if not re.match(r"^OL\d+[A-Z]?$", cleaned_key):
                cleaned_key = None

        return {"name": cleaned_name, "ol_author_key": cleaned_key}

    @staticmethod
    def merge_author_sources(
        gb_info: Dict,
        ol_info: Dict,
    ) -> List[Dict]:
        """
        Merge author data from Google Books and Open Library APIs.

        Strategy:
        1. Use Open Library as PRIMARY source (has author keys for deduplication)
        2. Match Google Books authors to Open Library authors via fuzzy matching
        3. Add any Google Books authors not found in Open Library
        4. Deduplicate final list

        Args:
            gb_info: Dictionary containing Google Books author data
            ol_info: Dictionary containing Open Library author data

        Returns:
            List of merged, deduplicated author records
        """
        gb_authors = gb_info.get("authors", [])
        ol_authors = ol_info.get("author_name", [])
        openlibrary_keys = ol_info.get("author_key", [])

        if not gb_authors or not ol_authors:
            return []

        merged_authors = []
        processed_google_indices = set()

        # Phase 1: Process Open Library authors
        if ol_authors and openlibrary_keys:
            for ol_idx, ol_name in enumerate(ol_authors):
                ol_key = (
                    openlibrary_keys[ol_idx] if ol_idx < len(openlibrary_keys) else None
                )

                # Try to find matching Google Books author based on name and return the index of the matching author
                gb_match_idx = AuthorTransformer._find_matching_author(
                    ol_name, gb_authors
                )

                if gb_match_idx is not None:
                    processed_google_indices.add(gb_match_idx)
                    # Use Google Books name (usually cleaner) but Open Library key
                    author = AuthorTransformer.transform_author_attributes(
                        gb_authors[gb_match_idx], ol_key
                    )
                else:
                    # No match in Google Books, use Open Library data
                    author = AuthorTransformer.transform_author_attributes(
                        ol_name, ol_key
                    )

                if author:
                    merged_authors.append(author)

        # Phase 2: Add remaining Google Books authors not matched
        for gb_idx, gb_name in enumerate(gb_authors):
            if gb_idx not in processed_google_indices:
                author = AuthorTransformer.transform_author_attributes(gb_name, None)
                if author:
                    # Check for duplicates before adding
                    is_duplicate = any(
                        AuthorTransformer._calculate_similarity(
                            author["name"], existing["name"]
                        )
                        > 0.85
                        for existing in merged_authors
                    )
                    if not is_duplicate:
                        merged_authors.append(author)

        return merged_authors
