from flask import render_template, request, redirect, flash, session

from . import student_profile_bp
from .services import *


@student_profile_bp.route("/student-profile")
def list_students():
    search = (request.args.get("search") or "").strip()
    status = request.args.get("status", "ALL")
    students = get_all_students(search=search, status=status)
    return render_template(
        "student_profile/list.html",
        students=students,
        search=search,
        status=status,
    )


@student_profile_bp.route("/student-profile/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        create_student(request.form)
        flash("Student record created", "success")
        return redirect("/student-profile")
    return render_template("student_profile/create.html")


@student_profile_bp.route("/student-profile/<ledger_no>")
def view(ledger_no):
    student = get_student(ledger_no)
    return render_template(
        "student_profile/view.html",
        student=student
    )


@student_profile_bp.route("/student-profile/<ledger_no>/edit", methods=["GET", "POST"])
def edit(ledger_no):
    student = get_student(ledger_no)
    if request.method == "POST":
        update_student(ledger_no, request.form)
        flash("Profile updated", "success")
        return redirect(f"/student-profile/{ledger_no}")
    return render_template("student_profile/edit.html", student=student)


@student_profile_bp.route("/student-profile/<ledger_no>/behaviour", methods=["GET", "POST"])
def behaviour(ledger_no):
    if request.method == "POST":
        user = (session.get("user") or {}).get("name", "System")
        add_behaviour_log(
            ledger_no,
            request.form["behaviour_type"],
            request.form["severity"],
            request.form["title"],
            request.form.get("description"),
            user
        )
        flash("Behaviour logged", "success")

    return render_template(
        "student_profile/behaviour_log.html",
        ledger_no=ledger_no,
        logs=get_behaviour_logs(ledger_no)
    )


@student_profile_bp.route("/student-profile/<ledger_no>/summary")
def summary(ledger_no):
    return render_template(
        "student_profile/summary.html",
        student=get_student(ledger_no),
        summary=get_student_summary(ledger_no)
    )


@student_profile_bp.route("/student-profile/<ledger_no>/timeline")
def timeline(ledger_no):
    return render_template(
        "student_profile/timeline.html",
        student=get_student(ledger_no),
        timeline=get_student_timeline(ledger_no)
    )


@student_profile_bp.route("/parent/student/<ledger_no>")
def parent_view(ledger_no):
    return render_template(
        "student_profile/parent_view.html",
        student=get_student(ledger_no),
        summary=get_student_summary(ledger_no)
    )
