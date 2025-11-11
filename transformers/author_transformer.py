"""
Class to extract and transform author strings into author dimension records.
"""

from typing import Optional


class AuthorTransformer:
    """
    Class to extract and transform author strings into author dimension records.
    """

    @staticmethod
    def transform_author_attributes(
        gb_info: Optional[dict], ol_info: Optional[dict]
    ) -> dict:
        """
        Transform an author string into an author dimension record.
        """

        author_name = gb_info.get("author_name", None)

        # 1. Handle null/empty author name
        if not author_name or not isinstance(author_name, str):
            return None

        return {"name": author_name}
