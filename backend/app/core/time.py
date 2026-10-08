from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (same value datetime.utcnow() returned, without its deprecation)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
