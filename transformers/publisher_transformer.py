"""
Class to extract and transform publisher strings into publisher dimension records.
"""

import re
from typing import Optional


class PublisherTransformer:
    """
    Class to extract and transform publisher strings into publisher dimension records.
    """

    @staticmethod
    def transform_publisher_attributes(gb_info: Optional[dict]) -> dict:
        """
        Clean and standardize publisher string for warehouse loading.

        Steps:
        1. Handle nulls / empties
        2. Normalize whitespace
        3. Normalize casing (smart title case only if needed)
        4. Normalize legal entity suffixes (Ltd, Inc, etc.)
        5. Clean punctuation and commas
        6. Provide ASCII version for search
        """

        publisher_str = gb_info.get("publisher", None)
        if not publisher_str or not isinstance(publisher_str, str):
            return {"name": None}

        # 1. Basic whitespace cleanup
        cleaned = " ".join(publisher_str.strip().split())
        if not cleaned:
            return {"name": None}

        # 2. Smart case normalization (only if fully uppercase/lowercase)
        if cleaned.isupper() or cleaned.islower():
            cleaned = cleaned.title()

        # 3. Normalize legal suffixes
        suffix_map = {
            r"\bLTD\.?\b": "Ltd",
            r"\bINC\.?\b": "Inc",
            r"\bLLC\.?\b": "LLC",
            r"\bCO\.?\b": "Co",
            r"\bCORPORATION\b": "Corporation",
            r"\bLIMITED\b": "Limited",
        }
        for pattern, repl in suffix_map.items():
            cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)

        # 4. Remove trailing commas or periods
        cleaned = re.sub(r"[.,;:\s]+$", "", cleaned).strip()

        # 5. Optional: remove region suffix (U.S., UK) *only* if isolated
        cleaned = re.sub(
            r"\b(U\.?S\.?|UK|EU|CA|AU)\b$", "", cleaned, flags=re.IGNORECASE
        ).strip()

        return {"name": cleaned}
