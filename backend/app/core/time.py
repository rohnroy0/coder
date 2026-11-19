from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (same value datetime.utcnow() returned, without its deprecation)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize any datetime to naive UTC. Aware values are CONVERTED to UTC
    before the tzinfo is dropped - stripping tzinfo without converting would
    silently shift the moment by the client's UTC offset. Naive values are
    assumed to already be UTC and pass through unchanged."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
