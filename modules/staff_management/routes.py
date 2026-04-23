from flask import render_template, request, redirect, url_for, flash
from . import staff_management_bp
from .services import (
    get_all_staff,
    get_staff_by_id,
    create_staff,
    update_staff
)


@staff_management_bp.route("/staff")
def staff_list():
    status = request.args.get("status", "ACTIVE")
    search = (request.args.get("search") or "").strip()
    role = (request.args.get("role") or "").strip()
    staff_code = (request.args.get("staff_code") or "").strip()
    department = (request.args.get("department") or "").strip()
    phone = (request.args.get("phone") or "").strip()

    staff_rows = get_all_staff(
        status=status,
        search=search,
        role=role,
        staff_code=staff_code,
        department=department,
        phone=phone,
    )
    return render_template(
        "staff_management/list.html",
        staff_rows=staff_rows,
        status=status,
        search=search,
        role=role,
        staff_code=staff_code,
        department=department,
        phone=phone,
    )


@staff_management_bp.route("/staff/create", methods=["GET", "POST"])
def staff_create():
    if request.method == "POST":
        ok, msg = create_staff(request.form)
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("staff_management.staff_list"))
    return render_template("staff_management/create.html")


@staff_management_bp.route("/staff/<int:staff_id>/view")
def staff_view(staff_id):
    staff = get_staff_by_id(staff_id)
    if not staff:
        flash("❌ Staff not found", "danger")
        return redirect(url_for("staff_management.staff_list"))
    return render_template("staff_management/view.html", staff=staff)


@staff_management_bp.route("/staff/<int:staff_id>/edit", methods=["GET", "POST"])
def staff_edit(staff_id):
    staff = get_staff_by_id(staff_id)
    if not staff:
        flash("❌ Staff not found", "danger")
        return redirect(url_for("staff_management.staff_list"))

    if request.method == "POST":
        ok, msg = update_staff(staff_id, request.form)
        flash(msg, "success" if ok else "danger")
        return redirect(url_for("staff_management.staff_view", staff_id=staff_id))

    return render_template("staff_management/edit.html", staff=staff)
