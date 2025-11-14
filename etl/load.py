from typing import Dict, Any
from logging import Logger
from supabase import Client

from loader.general_loader import GeneralLoader


class Loader:
    """Load transformed book data into the dimensional warehouse."""

    @staticmethod
    def load_independent_dimensions(
        logger: Logger,
        independent_dimensions: Dict[str, Any],
    ) -> Dict[str, Any]:

        dim_response = {}
        dict_dimensions = {"dim_date", "dim_publisher"}
        list_dimensions = {"dim_author", "dim_genre"}
        for dim_name, dim_data in independent_dimensions.items():
            # when there's no data in a dimension like genre etc
            if dim_data == [] or dim_data is None:
                dim_response[dim_name] = []
                continue

            if dim_name in dict_dimensions:
                dim_data = [dim_data]

            response_data = GeneralLoader.load_independent_dimensions(
                dim_name, dim_data
            )

            dim_response[dim_name] = response_data

        return dim_response

    @staticmethod
    def load_dim_books(
        logger: Logger, supabase_client: Client, book_dimension: Dict[str, Any]
    ) -> None:
        supabase_client.table("dim_books").insert(book_dimension).execute()

    @staticmethod
    def load_book_author_bridge(
        logger: Logger, supabase_client: Client, book_dimension: Dict[str, Any]
    ) -> None:
        supabase_client.table("book_author_bridge").insert(book_dimension).execute()

    @staticmethod
    def load_book_genre_bridge(
        logger: Logger, supabase_client: Client, book_dimension: Dict[str, Any]
    ) -> None:
        supabase_client.table("book_genre_bridge").insert(book_dimension).execute()
