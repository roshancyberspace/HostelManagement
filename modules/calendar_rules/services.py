import calendar
from datetime import datetime, timedelta
from urllib.request import urlopen

from models.db import get_db


DEFAULT_INDIA_HOLIDAY_FEED = "https://www.officeholidays.com/ics-clean/india"

SUGGESTED_HOLIDAYS = [
    {"slug": "ambedkar-2025", "date": "2025-04-14", "day_type": "GOVT_HOLIDAY", "title": "Dr. Babasaheb Ambedkar Jayanti", "description": "Suggested government holiday"},
    {"slug": "independence-2025", "date": "2025-08-15", "day_type": "GOVT_HOLIDAY", "title": "Independence Day", "description": "Suggested government holiday"},
    {"slug": "gandhi-2025", "date": "2025-10-02", "day_type": "GOVT_HOLIDAY", "title": "Mahatma Gandhi Birthday", "description": "Suggested government holiday"},
    {"slug": "republic-2026", "date": "2026-01-26", "day_type": "GOVT_HOLIDAY", "title": "Republic Day", "description": "Suggested government holiday"},
    {"slug": "holi-2025", "date": "2025-03-14", "day_type": "FESTIVAL_HOLIDAY", "title": "Holi", "description": "Suggested festival holiday"},
    {"slug": "ram-navami-2025", "date": "2025-04-06", "day_type": "FESTIVAL_HOLIDAY", "title": "Ram Navami", "description": "Suggested festival holiday"},
    {"slug": "mahavir-2025", "date": "2025-04-10", "day_type": "FESTIVAL_HOLIDAY", "title": "Mahavir Jayanti", "description": "Suggested festival holiday"},
    {"slug": "buddha-2025", "date": "2025-05-12", "day_type": "FESTIVAL_HOLIDAY", "title": "Buddha Purnima", "description": "Suggested festival holiday"},
    {"slug": "bakrid-2025", "date": "2025-06-07", "day_type": "FESTIVAL_HOLIDAY", "title": "Bakrid", "description": "Suggested festival holiday"},
    {"slug": "rakhi-2025", "date": "2025-08-09", "day_type": "FESTIVAL_HOLIDAY", "title": "Raksha Bandhan", "description": "Suggested festival holiday"},
    {"slug": "janmashtami-2025", "date": "2025-08-16", "day_type": "FESTIVAL_HOLIDAY", "title": "Janmashtami", "description": "Suggested festival holiday"},
    {"slug": "milad-2025", "date": "2025-09-06", "day_type": "FESTIVAL_HOLIDAY", "title": "Maulud Nabi", "description": "Suggested festival holiday"},
    {"slug": "dussehra-2025", "date": "2025-10-02", "day_type": "FESTIVAL_HOLIDAY", "title": "Dussehra", "description": "Suggested festival holiday"},
    {"slug": "diwali-2025", "date": "2025-10-20", "day_type": "FESTIVAL_HOLIDAY", "title": "Diwali", "description": "Suggested festival holiday"},
    {"slug": "guru-nanak-2025", "date": "2025-11-05", "day_type": "FESTIVAL_HOLIDAY", "title": "Guru Nanak's Birthday", "description": "Suggested festival holiday"},
    {"slug": "christmas-2025", "date": "2025-12-25", "day_type": "FESTIVAL_HOLIDAY", "title": "Christmas Day", "description": "Suggested festival holiday"},
    {"slug": "maha-shivratri-2026", "date": "2026-02-15", "day_type": "FESTIVAL_HOLIDAY", "title": "Maha Shivratri", "description": "Suggested festival holiday"},
    {"slug": "holi-2026", "date": "2026-03-04", "day_type": "FESTIVAL_HOLIDAY", "title": "Holi", "description": "Suggested festival holiday"},
    {"slug": "eid-2026", "date": "2026-03-21", "day_type": "FESTIVAL_HOLIDAY", "title": "Eid-ul-Fitr", "description": "Suggested festival holiday"},
    {"slug": "mahavir-2026", "date": "2026-03-31", "day_type": "FESTIVAL_HOLIDAY", "title": "Mahavir Jayanti", "description": "Suggested festival holiday"},
]

GOVERNMENT_KEYWORDS = (
    "republic day",
    "independence day",
    "gandhi",
    "constitution",
    "ambedkar",
    "election",
)

FESTIVAL_KEYWORDS = (
    "holi",
    "diwali",
    "dussehra",
    "navratri",
    "eid",
    "bakrid",
    "ramzan",
    "muharram",
    "janmashtami",
    "ganesh",
    "chhath",
    "christmas",
    "guru nanak",
    "raksha bandhan",
    "mahavir",
    "buddha purnima",
)


def get_active_session():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT * FROM academic_sessions
        WHERE is_active = 1 AND is_deleted = 0
        LIMIT 1
    """)
    row = cur.fetchone()
    db.close()
    return row


def _parse_iso(date_value):
    return datetime.strptime(date_value, "%Y-%m-%d")


def _daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def _rule_exists(cur, session_id, from_date, to_date, day_type, title):
    cur.execute("""
        SELECT id
        FROM calendar_rules
        WHERE session_id = ?
          AND from_date = ?
          AND to_date = ?
          AND day_type = ?
          AND title = ?
          AND is_deleted = 0
        LIMIT 1
    """, (session_id, from_date, to_date, day_type, title))
    return cur.fetchone() is not None


def _insert_rule(cur, session_id, from_date, to_date, day_type, title, description=None):
    if _rule_exists(cur, session_id, from_date, to_date, day_type, title):
        return False

    cur.execute("""
        INSERT INTO calendar_rules
        (session_id, from_date, to_date, day_type, title, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, from_date, to_date, day_type, title, description))
    return True


def generate_sundays_for_session():
    session = get_active_session()
    if not session:
        return 0

    start = _parse_iso(session["start_date"])
    end = _parse_iso(session["end_date"])

    db = get_db()
    cur = db.cursor()
    created = 0

    for current in _daterange(start, end):
        if current.weekday() == 6:
            date_str = current.strftime("%Y-%m-%d")
            if _insert_rule(cur, session["id"], date_str, date_str, "SUNDAY", "Sunday", "Auto-generated weekly off"):
                created += 1

    db.commit()
    db.close()
    return created


def _classify_holiday_type(title):
    lower_title = (title or "").strip().lower()
    if any(keyword in lower_title for keyword in GOVERNMENT_KEYWORDS):
        return "GOVT_HOLIDAY"
    if any(keyword in lower_title for keyword in FESTIVAL_KEYWORDS):
        return "FESTIVAL_HOLIDAY"
    return "HOLIDAY"


def _normalize_ics_lines(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized = []
    for line in lines:
        if line.startswith((" ", "\t")) and normalized:
            normalized[-1] += line[1:]
        else:
            normalized.append(line)
    return normalized


def _parse_ics_events(text):
    events = []
    current = None
    for line in _normalize_ics_lines(text):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            if current and current.get("summary") and current.get("date"):
                events.append(current)
            current = None
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            base_key = key.split(";", 1)[0]
            if base_key == "SUMMARY":
                current["summary"] = value.strip()
            elif base_key == "DTSTART":
                current["date"] = value.strip()[:8]
    return events


def import_holiday_feed(feed_url=None):
    session = get_active_session()
    if not session:
        raise Exception("No active academic session")

    target_url = (feed_url or DEFAULT_INDIA_HOLIDAY_FEED).strip()
    if not target_url:
        raise Exception("Holiday feed URL is required")

    start = _parse_iso(session["start_date"])
    end = _parse_iso(session["end_date"])

    try:
        with urlopen(target_url, timeout=20) as response:
            text = response.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        raise Exception(f"Holiday feed import failed: {exc}")

    events = _parse_ics_events(text)
    if not events:
        raise Exception("No holidays found in the selected calendar feed")

    db = get_db()
    cur = db.cursor()
    created = 0

    for event in events:
        event_date = datetime.strptime(event["date"], "%Y%m%d")
        if not (start <= event_date <= end):
            continue

        date_str = event_date.strftime("%Y-%m-%d")
        title = event["summary"]
        day_type = _classify_holiday_type(title)
        description = f"Imported from holiday feed: {target_url}"

        if _insert_rule(cur, session["id"], date_str, date_str, day_type, title, description):
            created += 1

    db.commit()
    db.close()
    return created


def create_rule(from_date, to_date, day_type, title, description):
    session = get_active_session()
    if not session:
        raise Exception("No active academic session")

    if not from_date or not to_date or not day_type or not title:
        raise Exception("Please fill all required fields")

    start = _parse_iso(from_date)
    end = _parse_iso(to_date)
    if start > end:
        raise Exception("From date cannot be after To date")

    session_start = _parse_iso(session["start_date"])
    session_end = _parse_iso(session["end_date"])
    if start < session_start or end > session_end:
        raise Exception("Selected dates must stay inside the active academic session")

    db = get_db()
    cur = db.cursor()
    inserted = _insert_rule(cur, session["id"], from_date, to_date, day_type, title.strip(), (description or "").strip() or None)
    db.commit()
    db.close()

    if not inserted:
        raise Exception("Same calendar rule already exists")


def get_all_rules():
    session = get_active_session()
    if not session:
        return []

    generate_sundays_for_session()

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM calendar_rules
        WHERE session_id = ?
          AND is_deleted = 0
        ORDER BY from_date, title
    """, (session["id"],))
    rows = cur.fetchall()
    db.close()
    return rows


def get_rule_dashboard_data(month_value=None):
    session = get_active_session()
    if not session:
        return {
            "summary": {"total": 0, "sundays": 0, "holidays": 0, "manual": 0},
            "month_value": month_value or "",
            "calendar_days": [],
        }

    rules = get_all_rules()
    summary = {
        "total": len(rules),
        "sundays": sum(1 for rule in rules if rule["day_type"] == "SUNDAY"),
        "holidays": sum(1 for rule in rules if "HOLIDAY" in rule["day_type"] or rule["day_type"] == "HOLIDAY"),
        "manual": sum(1 for rule in rules if rule["day_type"] != "SUNDAY"),
    }

    if month_value:
        target_month = datetime.strptime(f"{month_value}-01", "%Y-%m-%d")
    else:
        target_month = _parse_iso(session["start_date"])
        month_value = target_month.strftime("%Y-%m")

    cal = calendar.Calendar(firstweekday=0)
    first_day = target_month.replace(day=1)
    month_dates = list(cal.itermonthdates(first_day.year, first_day.month))

    rule_map = {}
    for rule in rules:
        current = _parse_iso(rule["from_date"])
        end = _parse_iso(rule["to_date"])
        while current <= end:
            key = current.strftime("%Y-%m-%d")
            rule_map.setdefault(key, []).append(rule)
            current += timedelta(days=1)

    calendar_days = []
    for day in month_dates:
        key = day.strftime("%Y-%m-%d")
        day_rules = rule_map.get(key, [])
        calendar_days.append({
            "date": key,
            "day": day.day,
            "in_month": day.month == first_day.month,
            "rules": day_rules,
            "primary_type": day_rules[0]["day_type"] if day_rules else "WORKING",
        })

    prev_month = (target_month.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    if target_month.month == 12:
        next_month = target_month.replace(year=target_month.year + 1, month=1, day=1).strftime("%Y-%m")
    else:
        next_month = target_month.replace(month=target_month.month + 1, day=1).strftime("%Y-%m")

    return {
        "summary": summary,
        "month_value": month_value,
        "calendar_days": calendar_days,
        "default_feed_url": DEFAULT_INDIA_HOLIDAY_FEED,
        "selected_month_label": target_month.strftime("%B %Y"),
        "prev_month": prev_month,
        "next_month": next_month,
    }


def get_suggested_holidays():
    session = get_active_session()
    if not session:
        return {"govt": [], "festival": []}

    session_start = _parse_iso(session["start_date"])
    session_end = _parse_iso(session["end_date"])
    rules = get_all_rules()
    existing_keys = {(rule["from_date"], rule["title"], rule["day_type"]) for rule in rules}

    govt = []
    festival = []
    for item in SUGGESTED_HOLIDAYS:
        date_obj = _parse_iso(item["date"])
        if not (session_start <= date_obj <= session_end):
            continue

        enriched = dict(item)
        enriched["exists"] = (item["date"], item["title"], item["day_type"]) in existing_keys
        if item["day_type"] == "GOVT_HOLIDAY":
            govt.append(enriched)
        else:
            festival.append(enriched)

    govt.sort(key=lambda item: item["date"])
    festival.sort(key=lambda item: item["date"])
    return {"govt": govt, "festival": festival}


def get_monthly_holiday_focus(month_value=None):
    session = get_active_session()
    if not session:
        return {"govt": [], "festival": []}

    if month_value:
        selected_month = datetime.strptime(f"{month_value}-01", "%Y-%m-%d")
    else:
        selected_month = _parse_iso(session["start_date"])

    suggested = get_suggested_holidays()

    def _same_month(items):
        result = []
        for item in items:
            item_date = _parse_iso(item["date"])
            if item_date.year == selected_month.year and item_date.month == selected_month.month:
                result.append(item)
        return result

    return {
        "govt": _same_month(suggested["govt"]),
        "festival": _same_month(suggested["festival"]),
    }


def create_suggested_rule(slug):
    match = next((item for item in SUGGESTED_HOLIDAYS if item["slug"] == slug), None)
    if not match:
        raise Exception("Suggested holiday not found")

    create_rule(
        match["date"],
        match["date"],
        match["day_type"],
        match["title"],
        match["description"],
    )


def can_delete_rule(rule_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT day_type, title FROM calendar_rules
        WHERE id = ? AND is_deleted = 0
    """, (rule_id,))
    row = cur.fetchone()
    db.close()

    if not row:
        return False, "Rule not found"

    if row["day_type"] == "SUNDAY":
        return False, "Sunday weekly offs are auto-managed and cannot be deleted"

    return True, ""


def soft_delete_rule(rule_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE calendar_rules
        SET is_deleted = 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (rule_id,))

    db.commit()
    db.close()
