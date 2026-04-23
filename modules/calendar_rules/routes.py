from flask import render_template, request, redirect, url_for, flash, session
from services.rbac import has_permission
from . import calendar_rules_bp
from .services import (
    get_all_rules,
    create_rule,
    can_delete_rule,
    soft_delete_rule,
    get_active_session,
    get_rule_dashboard_data,
    import_holiday_feed,
    DEFAULT_INDIA_HOLIDAY_FEED,
    get_suggested_holidays,
    create_suggested_rule,
    get_monthly_holiday_focus
)


def superintendent_only():
    return has_permission("calendar_rules.manage")


@calendar_rules_bp.route("/")
def index():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    rules = get_all_rules()
    active_session = get_active_session()
    month_value = request.args.get("month")
    dashboard = get_rule_dashboard_data(month_value)

    return render_template(
        "calendar_rules/index.html",
        rules=rules,
        active_session=active_session,
        dashboard=dashboard,
        default_feed_url=DEFAULT_INDIA_HOLIDAY_FEED,
        suggested_holidays=get_suggested_holidays(),
        monthly_focus=get_monthly_holiday_focus(dashboard["month_value"])
    )


@calendar_rules_bp.route("/create", methods=["POST"])
def create():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    try:
        create_rule(
            request.form.get("from_date"),
            request.form.get("to_date"),
            request.form.get("day_type"),
            request.form.get("title"),
            request.form.get("description")
        )
        flash("Calendar rule added successfully", "success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("calendar_rules.index"))


@calendar_rules_bp.route("/sync-holidays", methods=["POST"])
def sync_holidays():
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    try:
        created = import_holiday_feed(request.form.get("feed_url"))
        flash(f"Holiday sync complete. {created} new holiday rule(s) imported.", "success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("calendar_rules.index"))


@calendar_rules_bp.route("/add-suggested/<slug>", methods=["POST"])
def add_suggested(slug):
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    try:
        create_suggested_rule(slug)
        flash("Suggested holiday added.", "success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("calendar_rules.index"))


@calendar_rules_bp.route("/delete/<int:rule_id>")
def delete(rule_id):
    if not superintendent_only():
        flash("Unauthorized access", "danger")
        return redirect(url_for("dashboard"))

    ok, msg = can_delete_rule(rule_id)
    if not ok:
        flash(msg, "danger")
        return redirect(url_for("calendar_rules.index"))

    soft_delete_rule(rule_id)
    flash("Rule deleted safely", "success")
    return redirect(url_for("calendar_rules.index"))
