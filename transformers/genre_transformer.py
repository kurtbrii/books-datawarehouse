# transformers/genre_transformer.py
import re
from typing import Optional, List, Dict


class GenreTransformer:
    """
    Clean and standardize genre/category data for warehouse loading.
    """

    @staticmethod
    def transform_genre(gb_info: Dict) -> Optional[str]:
        """
        Clean and normalize a single genre name.

        Args:
            genre_name: Raw genre/category name from API

        Returns:
            Cleaned genre name in lowercase, or None if invalid
        """

        genres = gb_info.get("categories", [])

        cleaned_genres = []

        for genre_name in genres:
            # 1. Handle null/empty
            if not genre_name or not isinstance(genre_name, str):
                return None

            # 2. Strip whitespace
            cleaned = genre_name.strip()
            if not cleaned:
                return None

            # 3. Normalize to lowercase
            cleaned = cleaned.lower()

            # 4. Normalize whitespace (multiple spaces → single space)
            cleaned = " ".join(cleaned.split())

            # 5. Remove common API prefixes (optional)
            # Google Books sometimes includes "FICTION / " prefix
            cleaned = re.sub(r"^(fiction|non-fiction)\s*/\s*", "", cleaned)

            # 6. Validate length (genres shouldn't be too long)
            if len(cleaned) > 100:
                return None

            cleaned_genres.append(cleaned)

        return cleaned_genres
