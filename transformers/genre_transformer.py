# transformers/genre_transformer.py
import re
from typing import Optional, List, Dict


class GenreTransformer:
    """
    Clean and standardize genre/category data for warehouse loading.
    """

    @staticmethod
    def transform_genre(gb_info: Dict) -> List[Dict]:
        """
        Clean and normalize genre names into dimension records.

        Args:
            gb_info: Google Books info dictionary containing categories

        Returns:
            List of genre dimension records (dicts with 'name' key)
        """

        genres = gb_info.get("categories", [])

        cleaned_genres = []

        for genre_name in genres:
            # 1. Handle null/empty
            if not genre_name or not isinstance(genre_name, str):
                continue

            # 2. Strip whitespace
            cleaned = genre_name.strip()
            if not cleaned:
                continue

            # 3. Normalize to lowercase
            cleaned = cleaned.lower()

            # 4. Normalize whitespace (multiple spaces → single space)
            cleaned = " ".join(cleaned.split())

            # 5. Remove common API prefixes (optional)
            # Google Books sometimes includes "FICTION / " prefix
            cleaned = re.sub(r"^(fiction|non-fiction)\s*/\s*", "", cleaned)

            # 6. Validate length (genres shouldn't be too long)
            if len(cleaned) > 100:
                continue

            cleaned_genres.append({"genre_name": cleaned})

        return cleaned_genres
