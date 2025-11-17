from supabase import Client
from typing import Dict, Any, List
from datetime import datetime, timezone
from helpers.constants import CONFLICT_COLUMNS

from config import Config


class GeneralLoader:
    supabase_client: Client = Config.get_supabase_client()

    @staticmethod
    def load_independent_dimensions(
        table_name: str,
        independent_dimensions: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        if table_name != "dim_date":
            for row in independent_dimensions:
                row["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Map table names to their conflict columns for upsert
        on_conflict = CONFLICT_COLUMNS.get(table_name)
        response = (
            GeneralLoader.supabase_client.table(table_name)
            .upsert(independent_dimensions, on_conflict=on_conflict)
            .execute()
        )

        return response.data

    @staticmethod
    def general_loader(
        table_name: str,
        meta_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        This method is used by both the general loader and the fact table loader.

        fact_book_metrics has updated_at column, and the bridge tables do not have it.
        """

        on_conflict = CONFLICT_COLUMNS.get(table_name)

        if table_name == "fact_book_metrics":
            meta_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        response = (
            GeneralLoader.supabase_client.table(table_name)
            .upsert(meta_data, on_conflict=on_conflict)
            .execute()
        )

        return response.data
