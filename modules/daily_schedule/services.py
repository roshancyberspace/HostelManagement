from datetime import datetime

from modules.hostel_timetable.services import get_timetable
from modules.mess_menu.services import get_active_weekly_menu


MEAL_MAP = {
    "breakfast": "breakfast",
    "brunch": "brunch",
    "lunch": "lunch",
    "evening snacks": "evening_snacks",
    "snacks": "evening_snacks",
    "dinner": "dinner",
}


def format_clock(value):
    if not value:
        return ""

    for pattern in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, pattern).strftime("%I:%M %p")
        except ValueError:
            continue
    return value


def build_time_range(start, end):
    start_label = format_clock(start)
    end_label = format_clock(end)

    if start_label and end_label:
        return f"{start_label} - {end_label}"
    return start_label or end_label or "Time not set"


def detect_menu_field(activity_name):
    lowered = (activity_name or "").lower()
    for key, field in MEAL_MAP.items():
        if key in lowered:
            return field
    return None


def get_menu_for_day(day_type, weekday):
    header, items = get_active_weekly_menu(day_type)
    if not header:
        return {}

    for row in items:
        if row["day_name"] == weekday:
            return {
                "breakfast": row["breakfast"],
                "brunch": row["brunch"],
                "lunch": row["lunch"],
                "evening_snacks": row["evening_snacks"],
                "dinner": row["dinner"],
            }
    return {}


def build_daily_schedule(day_type, weekday):
    timetable = get_timetable(day_type)
    menu = get_menu_for_day(day_type, weekday)

    result = []
    for row in timetable:
        menu_field = detect_menu_field(row["activity_name"])
        menu_text = menu.get(menu_field) if menu_field else None

        result.append({
            "time": build_time_range(row["resolved_start"], row["resolved_end"]),
            "activity": row["activity_name"],
            "menu": menu_text or "No menu linked",
            "has_menu": bool(menu_text),
            "is_meal": bool(menu_field),
            "source": (row["time_source"] or "MANUAL").replace("_", " ").title(),
            "sequence_no": row["sequence_no"],
        })

    return result
