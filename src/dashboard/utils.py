# src/dashboard/utils.py

from datetime import datetime


def format_signal_date(timestamp: str) -> str:
    """
    Format an ISO timestamp string to a human-readable date format.

    Args:
        timestamp: ISO timestamp string (e.g., "2026-01-16T15:42:55.327195+00:00")

    Returns:
        Formatted date string (e.g., "Jan 16, 2026") or "Unknown date" if invalid
    """
    if not timestamp:
        return "Unknown date"

    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return "Unknown date"