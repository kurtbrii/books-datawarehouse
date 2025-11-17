from typing import Dict, Any, List
from datetime import datetime, timezone
from logging import Logger

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
        logger.info("💾 Loading independent dimensions...")

        try:
            dims_pk = {}
            dict_dimensions = {"dim_date", "dim_publisher"}
            for dim_name, dim_data in independent_dimensions.items():
                dims_pk[dim_name] = []
                # when there's no data in a dimension like genre etc
                if dim_data == [] or dim_data is None:
                    logger.info("⏭️ Skipping empty dimension: %s", dim_name)
                    continue

                logger.info("📤 Loading dimension: %s", dim_name)

                if dim_name in dict_dimensions:
                    dim_data = [dim_data]

                response_data = GeneralLoader.load_independent_dimensions(
                    dim_name, dim_data
                )

                # load the primary key of the dimension into the dictionary
                for row in response_data:
                    dim_id = get_id_name(dim_name)
                    dims_pk[dim_name].append(row[dim_id])

                logger.info("✅ Loaded dimension: %s", dim_name)

            logger.info("✅ Independent dimensions loaded successfully")
            return dims_pk

        except Exception as e:
            logger.error("❌ Failed to load independent dimensions: %s", str(e))
            raise

    @staticmethod
    def load_dim_books(
        logger: Logger,
        metadata: Dict[str, Any],
    ) -> str:
        """Load book dimension to warehouse."""
        logger.info("📚 Loading book dimension...")

        try:
            date_updated = datetime.now(timezone.utc).isoformat()
            metadata["updated_at"] = date_updated

            response_data = GeneralLoader.general_loader(
                table_name="dim_books",
                meta_data=metadata,
            )

            isbn = response_data[0]["isbn"]
            logger.info("✅ Book dimension loaded successfully for ISBN: %s", isbn)
            return isbn

        except Exception as e:
            logger.error("❌ Failed to load book dimension: %s", str(e))
            raise

    @staticmethod
    def load_bridge_tables(
        logger: Logger,
        bridge_table_name: str,
        book_isbn: str,
        bridge_dim_ids: List[str],
        bridge_dim_name: str,
    ) -> None:
        """Load bridge table relationships (many-to-many)."""
        logger.info(
            "🌉 Loading bridge table: %s (%d relationships)...",
            bridge_table_name,
            len(bridge_dim_ids),
        )

        try:
            for idx, dim_id in enumerate(bridge_dim_ids, 1):
                GeneralLoader.general_loader(
                    table_name=bridge_table_name,
                    meta_data={
                        "isbn": book_isbn,
                        f"{bridge_dim_name}_id": dim_id,
                    },
                )
                logger.info(
                    "📌 Loaded relationship %d/%d for %s",
                    idx,
                    len(bridge_dim_ids),
                    bridge_table_name,
                )

            logger.info("✅ Bridge table loaded successfully: %s", bridge_table_name)

        except Exception as e:
            logger.error(
                "❌ Failed to load bridge table %s: %s", bridge_table_name, str(e)
            )
            raise

    @staticmethod
    def load_fact_table(
        logger: Logger,
        fact_table_name: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Load fact table with book metrics."""
        logger.info("📊 Loading fact table: %s...", fact_table_name)

        try:
            response_data = GeneralLoader.general_loader(
                fact_table_name,
                metadata,
            )

            metric_id = response_data[0]["metric_id"]
            logger.info(
                "✅ Fact table loaded successfully: %s (metric_id: %s)",
                fact_table_name,
                metric_id,
            )
            return metric_id

        except Exception as e:
            logger.error("❌ Failed to load fact table %s: %s", fact_table_name, str(e))
            raise
