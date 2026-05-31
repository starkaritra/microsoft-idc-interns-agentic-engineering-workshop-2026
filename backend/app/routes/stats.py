"""Stats routes — daily averages, weekly averages, heatmap data."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median

from fastapi import APIRouter

from ..storage import list_entries

router = APIRouter()


@router.get("/stats/daily")
def daily_stats():
    """Daily mood & energy averages for the last 14 days."""
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=13)
    entries = list_entries(start_date=str(start))

    by_day: dict[str, list] = defaultdict(list)
    for e in entries:
        day = str(e.timestamp.date())
        by_day[day].append(e)

    result = []
    for i in range(14):
        day = str(start + timedelta(days=i))
        day_entries = by_day.get(day, [])
        result.append(
            {
                "date": day,
                "avg_mood": (
                    round(sum(e.mood for e in day_entries) / len(day_entries), 1)
                    if day_entries
                    else None
                ),
                "avg_energy": (
                    round(sum(e.energy for e in day_entries) / len(day_entries), 1)
                    if day_entries
                    else None
                ),
                "count": len(day_entries),
            }
        )
    return result


@router.get("/stats/weekly")
def weekly_stats():
    """Weekly mood & energy averages for the last 8 weeks."""
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(weeks=8)
    entries = list_entries(start_date=str(start))

    by_week: dict[str, list] = defaultdict(list)
    for e in entries:
        week_start = e.timestamp.date() - timedelta(days=e.timestamp.weekday())
        by_week[str(week_start)].append(e)

    result = []
    for i in range(8):
        week_start = start + timedelta(weeks=i) - timedelta(
            days=(start + timedelta(weeks=i)).weekday()
        )
        key = str(week_start)
        week_entries = by_week.get(key, [])
        result.append(
            {
                "week_start": key,
                "avg_mood": (
                    round(sum(e.mood for e in week_entries) / len(week_entries), 1)
                    if week_entries
                    else None
                ),
                "avg_energy": (
                    round(sum(e.energy for e in week_entries) / len(week_entries), 1)
                    if week_entries
                    else None
                ),
                "count": len(week_entries),
            }
        )
    return result


@router.get("/stats/heatmap")
def heatmap_data():
    """Calendar heatmap data — average mood per day for the last 90 days."""
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=89)
    entries = list_entries(start_date=str(start))

    by_day: dict[str, list] = defaultdict(list)
    for e in entries:
        day = str(e.timestamp.date())
        by_day[day].append(e)

    result = []
    for i in range(90):
        day = str(start + timedelta(days=i))
        day_entries = by_day.get(day, [])
        avg_mood = (
            round(sum(e.mood for e in day_entries) / len(day_entries), 1)
            if day_entries
            else None
        )
        result.append({"date": day, "avg_mood": avg_mood, "count": len(day_entries)})
    return result


@router.get("/stats/retention")
def retention_stats():
    """Honest single-user retention metrics."""
    today = datetime.now(timezone.utc).date()
    entries = list_entries()
    day_set = {e.timestamp.date() for e in entries}

    last_7d = sum(1 for i in range(7) if (today - timedelta(days=i)) in day_set)
    last_30d = sum(1 for i in range(30) if (today - timedelta(days=i)) in day_set)

    # current streak: consecutive days ending today (or yesterday)
    def streak_from(start):
        d = start
        s = 0
        while d in day_set:
            s += 1
            d -= timedelta(days=1)
        return s

    current_streak = streak_from(today)
    if current_streak == 0:
        current_streak = streak_from(today - timedelta(days=1))

    # best streak (over all history)
    best_streak = 0
    if day_set:
        sorted_days = sorted(day_set)
        run = 1
        best_streak = 1
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i - 1]).days == 1:
                run += 1
                best_streak = max(best_streak, run)
            else:
                run = 1

    # entries per active week median (last 30 days, only weeks with activity)
    by_week: dict = defaultdict(int)
    cutoff = today - timedelta(days=30)
    for e in entries:
        d = e.timestamp.date()
        if d < cutoff or d > today:
            continue
        week_start = d - timedelta(days=d.weekday())
        by_week[week_start] += 1
    weekly_counts = [v for v in by_week.values() if v > 0]
    entries_per_active_week_median = (
        float(median(weekly_counts)) if weekly_counts else 0.0
    )

    return {
        "last_7d_active_days": last_7d,
        "last_30d_active_days": last_30d,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "entries_per_active_week_median": entries_per_active_week_median,
    }
