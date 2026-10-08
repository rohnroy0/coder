from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BadgeCatalogItem(BaseModel):
    code: str
    name: str
    description: str
    icon: str


class EarnedBadge(BadgeCatalogItem):
    earned_at: datetime


class BadgeStatus(BadgeCatalogItem):
    earned: bool
    earned_at: Optional[datetime] = None
    unlock_hint: Optional[str] = None  # how close the student is; None once earned
