# CONTEXT PROCESSORS ONLY (NO BLUEPRINTS HERE)

from services.notification_service import get_notification_counts

def inject_notifications():
    """
    Inject notification counters into all templates.
    ALWAYS returns all keys to avoid Jinja crashes.
    """
    notify = get_notification_counts()

    # Absolute safety fallback
    return {
        "notify": {
            "overdue": notify.get("overdue", 0),
            "damages": notify.get("damages", 0),
            "gate_pass_pending": notify.get("gate_pass_pending", 0),
            "gate_pass_violations": notify.get("gate_pass_violations", 0),
        }
    }
