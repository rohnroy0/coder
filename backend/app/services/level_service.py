from typing import Dict

from app.core.config import settings

# (minimum level, title) pairs, applied in ascending order - a student's title is
# the highest-threshold entry their level has reached.
LEVEL_TITLES = [
    (1, "Novice"),
    (3, "Apprentice"),
    (6, "Coder"),
    (10, "Skilled Coder"),
    (15, "Expert"),
    (25, "Master"),
]


class LevelService:
    """
    Deliberately simple, transparent leveling curve: a flat number of points
    per level (settings.POINTS_PER_LEVEL), so a student's level is always
    derivable from their total points rather than stored and risking drift.
    """

    @staticmethod
    def _title_for(level: int) -> str:
        title = LEVEL_TITLES[0][1]
        for min_level, t in LEVEL_TITLES:
            if level >= min_level:
                title = t
        return title

    @staticmethod
    def compute_level(total_points: int) -> Dict:
        per_level = settings.POINTS_PER_LEVEL
        points = max(total_points, 0)  # penalties can push raw points negative; floor level at 1
        level = points // per_level + 1
        points_in_level = points % per_level

        return {
            "level": level,
            "level_title": LevelService._title_for(level),
            "points_in_level": points_in_level,
            "points_per_level": per_level,
            "level_progress_pct": round(points_in_level / per_level * 100.0, 1),
        }
