from flask import render_template, request, redirect, url_for, flash
from . import hostel_governance_bp
from .services import (
    create_notice,
    get_all_notices,
    acknowledge_notice,
    get_acknowledgements,
    record_decision,
    get_all_decisions
)

@hostel_governance_bp.route("/hostel-governance")
def dashboard():
    return render_template("hostel_governance/dashboard.html")


# ---------------- NOTICES ----------------

@hostel_governance_bp.route("/hostel-governance/notices")
def notice_list():
    notices = get_all_notices()
    return render_template("hostel_governance/notice_list.html", notices=notices)


@hostel_governance_bp.route("/hostel-governance/notices/create", methods=["GET", "POST"])
def create_notice_view():
    if request.method == "POST":
        create_notice(
            request.form["title"],
            request.form["content"],
            request.form["scope"],
            "Superintendent"
        )
        flash("Notice issued successfully", "success")
        return redirect(url_for("hostel_governance.notice_list"))

    return render_template("hostel_governance/create_notice.html")


@hostel_governance_bp.route("/hostel-governance/notices/<int:notice_id>/ack", methods=["GET", "POST"])
def acknowledge_notice_view(notice_id):
    if request.method == "POST":
        acknowledge_notice(notice_id, request.form["ledger_no"])
        flash("Acknowledged", "success")
        return redirect(url_for("hostel_governance.notice_list"))

    acknowledgements = get_acknowledgements(notice_id)
    return render_template(
        "hostel_governance/acknowledge_notice.html",
        notice_id=notice_id,
        acknowledgements=acknowledgements
    )


# ---------------- DECISIONS ----------------

@hostel_governance_bp.route("/hostel-governance/decisions", methods=["GET", "POST"])
def decision_register():
    if request.method == "POST":
        record_decision(
            request.form["ledger_no"],
            request.form["decision"],
            request.form.get("reference"),
            "Superintendent"
        )
        flash("Decision recorded", "success")

    decisions = get_all_decisions()
    return render_template("hostel_governance/decision_register.html", decisions=decisions)
