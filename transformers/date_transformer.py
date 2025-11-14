"""
DateTransformer class for extracting and transforming date strings into date dimension records.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from logging import Logger


class DateTransformer:
    """
    DateTransformer class for extracting and transforming date strings into date dimension records.
    """

    @staticmethod
    def transform_date_attributes(
        gb_info: Optional[dict], logger: Logger
    ) -> Optional[Dict[str, Any]]:
        """
        Extract and transform a date string into a date dimension record.

        Parses a date string and generates all necessary attributes for the dim_date table:
        - date_key: YYYYMMDD format (integer) for efficient joining
        - full_date: ISO format date for clarity
        - year, month, day: Temporal components
        - quarter: Q1-Q4 based on month
        - day_of_week: Monday-Sunday
        - is_weekend: Boolean flag for weekend/weekday

        Args:
            date_str: Date string (ISO format YYYY-MM-DD or variations)
            logger: Logger instance for audit trail

        Returns:
            Dict with all date dimension attributes, or None if date parsing fails

        Example:
            >>> date_record = extract_date_dimension('2017-10-10', logger)
            {
                'date_key': 20171010,
                'full_date': '2017-10-10',
                'year': 2017,
                'month': 10,
                'day': 10,
                'quarter': 'Q4',
                'day_of_week': 'Tuesday',
                'is_weekend': False
            }
        """

        date_str = gb_info.get("publishedDate", None)
        if not date_str:
            logger.debug("No date provided for date dimension extraction")
            return None

        try:
            # Parse date - handle common formats
            if isinstance(date_str, str):
                # Try ISO format first (YYYY-MM-DD)
                if len(date_str) == 10 and date_str.count("-") == 2:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                # Try year only format (YYYY)
                elif len(date_str) == 4 and date_str.isdigit():
                    parsed_date = datetime.strptime(date_str, "%Y").date()
                # Try year-month format (YYYY-MM)
                elif len(date_str) == 7 and date_str.count("-") == 1:
                    parsed_date = datetime.strptime(date_str, "%Y-%m").date()
                else:
                    logger.warning(f"Unexpected date format: {date_str}")
                    return None
            else:
                parsed_date = date_str

            # Calculate derived attributes
            date_key = int(parsed_date.strftime("%Y%m%d"))
            month = parsed_date.month
            quarter = f"Q{(month - 1) // 3 + 1}"

            # Get day of week name
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            day_of_week = day_names[parsed_date.weekday()]
            is_weekend = parsed_date.weekday() >= 5

            date_record = {
                "date_key": date_key,
                "full_date": parsed_date.isoformat(),
                "year": parsed_date.year,
                "month": month,
                "day": parsed_date.day,
                "quarter": quarter,
                "day_of_week": day_of_week,
                "is_weekend": is_weekend,
            }

            logger.debug(f"Extracted date dimension for {date_str}: {date_record}")
            return date_record

        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse date '{date_str}': {e}")
            return None
