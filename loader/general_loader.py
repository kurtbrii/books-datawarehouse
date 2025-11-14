from supabase import Client
from typing import Dict, Any, List
from datetime import datetime, timezone

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
        conflict_columns = {
            "dim_date": "date_key",
            "dim_publisher": "name",
            "dim_author": "ol_author_key",
            "dim_genre": "genre_name",
        }

        on_conflict = conflict_columns.get(table_name)

        response = (
            GeneralLoader.supabase_client.table(table_name)
            .upsert(independent_dimensions, on_conflict=on_conflict)
            .execute()
        )

        return response.data
