# -*- coding: utf-8 -*-
"""
Date utility functions for parsing and formatting dates.
"""
from datetime import datetime


def parse_date(date: str) -> str:
    """If a date string is set it parses it into a format YYYY-MM-DD. In case parsing fails None is returned.

    :param date: A string describing a date
    :return: A string in a format YYYY-MM-DD, an empty string, or None
    """
    if date == "":
        return date
    try:
        return datetime.fromisoformat(date).isoformat()
    except ValueError:
        return None

