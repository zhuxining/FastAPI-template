from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC timestamp with timezone information."""
    return datetime.now(UTC)
