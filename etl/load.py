from typing import Dict, Any, List
from logging import Logger
from supabase import Client
from datetime import datetime, timezone

from loader.general_loader import GeneralLoader
from helpers.utils import get_id_name


class Loader:
    """Load transformed book data into the dimensional warehouse."""

    @staticmethod
    def load_independent_dimensions(
        logger: Logger,
        independent_dimensions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Load the primary key of the dimension into the dictionary.
        """

        dims_pk = {}
        dict_dimensions = {"dim_date", "dim_publisher"}
        for dim_name, dim_data in independent_dimensions.items():
            dims_pk[dim_name] = []
            # when there's no data in a dimension like genre etc
            if dim_data == [] or dim_data is None:
                continue

            if dim_name in dict_dimensions:
                dim_data = [dim_data]

            response_data = GeneralLoader.load_independent_dimensions(
                dim_name, dim_data
            )

            # load the primary key of the dimension into the dictionary
            for row in response_data:
                dim_id = get_id_name(dim_name)
                dims_pk[dim_name].append(row[dim_id])

        return dims_pk

    @staticmethod
    def load_dim_books(
        logger: Logger,
        metadata: Dict[str, Any],
    ) -> str:

        date_updated = datetime.now(timezone.utc).isoformat()
        metadata["updated_at"] = date_updated

        response_data = GeneralLoader.general_loader(
            table_name="dim_books",
            meta_data=metadata,
        )

        return response_data[0]["isbn"]

    @staticmethod
    def load_bridge_tables(
        logger: Logger,
        bridge_table_name: str,
        book_isbn: str,
        bridge_dim_ids: List[str],
        bridge_dim_name: str,
    ) -> None:

        for dim_id in bridge_dim_ids:
            GeneralLoader.general_loader(
                table_name=bridge_table_name,
                meta_data={
                    "isbn": book_isbn,
                    f"{bridge_dim_name}_id": dim_id,
                },
            )
