"""Date range parsing and overlap-aware years of experience calculation."""

import re
from datetime import datetime
from dateutil import parser as date_parser


def parse_date_point(date_str: str | None) -> datetime | None:
    """Parse a date string into a datetime object.

    Handles 'Present', 'Current', 'Now', '2021-03', 'March 2021', '03/2021', '2021', etc.
    """
    if not date_str:
        return None

    cleaned = date_str.strip().lower()
    if cleaned in ("present", "current", "now", "ongoing"):
        return datetime.now()

    # Match 4-digit year only
    year_match = re.fullmatch(r"(\d{4})", cleaned)
    if year_match:
        return datetime(int(year_match.group(1)), 1, 1)

    try:
        # Default day to 1
        return date_parser.parse(date_str, default=datetime(2000, 1, 1))
    except Exception:
        return None


def calculate_experience_years(work_experiences: list[dict]) -> float:
    """Calculate total non-overlapping years of experience across work experience entries.

    Handles:
    - Overlapping roles without double counting
    - 'Present' / 'Current'
    - Missing start or end dates
    - Explicit duration_months fallback if dates are absent
    """
    intervals: list[tuple[datetime, datetime]] = []
    fallback_months = 0

    for exp in work_experiences:
        start_raw = exp.get("start_date")
        end_raw = exp.get("end_date")
        dur_months = exp.get("duration_months")

        start_dt = parse_date_point(start_raw)
        end_dt = parse_date_point(end_raw)

        if start_dt and end_dt:
            # Ensure start is before or equal to end
            if start_dt > end_dt:
                start_dt, end_dt = end_dt, start_dt
            intervals.append((start_dt, end_dt))
        elif dur_months and isinstance(dur_months, (int, float)) and dur_months > 0:
            fallback_months += int(dur_months)

    if not intervals and fallback_months > 0:
        return round(fallback_months / 12.0, 1)

    if not intervals:
        return 0.0

    # Sort intervals by start date
    intervals.sort(key=lambda x: x[0])

    # Merge overlapping intervals
    merged: list[tuple[datetime, datetime]] = [intervals[0]]
    for current_start, current_end in intervals[1:]:
        prev_start, prev_end = merged[-1]
        if current_start <= prev_end:
            # Overlap exists -> extend previous end date to max of both
            merged[-1] = (prev_start, max(prev_end, current_end))
        else:
            merged.append((current_start, current_end))

    # Calculate total days from merged intervals
    total_days = sum((end - start).days for start, end in merged)
    # Approximate years: 365.25 days per year
    total_years = max(0.0, total_days / 365.25)

    if fallback_months > 0:
        total_years += fallback_months / 12.0

    return round(total_years, 1)
