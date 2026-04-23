from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.rbac import (
    authenticate_user,
    can_access_path,
    create_permission,
    create_role,
    create_user,
    fetch_user_by_id,
    get_current_user,
    get_landing_path,
    get_permission_map,
    get_role_map,
    get_role_permissions_map,
    has_permission,
    list_permissions,
    list_roles,
    refresh_session_user,
    update_permission,
    update_role,
    update_own_profile,
    list_users,
    update_role_permissions,
    update_user,
)


auth_bp = Blueprint("auth", __name__)
rbac_bp = Blueprint("rbac", __name__)


@auth_bp.route("/auth/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(get_landing_path(session["user"]))

    if request.method == "POST":
        user_id = (request.form.get("user_id") or "").strip()
        password = request.form.get("password") or ""
        user = authenticate_user(user_id, password)
        if not user:
            flash("Invalid user ID or password.", "danger")
            return render_template("auth/login.html")

        session["user"] = user
        flash("Welcome back.", "success")
        next_url = request.args.get("next")
        if next_url and can_access_path(next_url, user):
            return redirect(next_url)
        return redirect(get_landing_path(user))

    return render_template("auth/login.html")


@auth_bp.route("/auth/forgot-password")
def forgot_password():
    if session.get("user"):
        return redirect(get_landing_path(session["user"]))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/auth/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/auth/profile", methods=["GET", "POST"])
def profile():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        ok, msg = update_own_profile(current_user["id"], request.form, request.files)
        flash(msg, "success" if ok else "danger")
        if ok:
            refresh_session_user()
            return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", current_user=current_user)


@rbac_bp.route("/rbac/users", methods=["GET", "POST"])
def users():
    if not has_permission("rbac.manage"):
        flash("You do not have permission to manage users.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        ok, msg = create_user(request.form, request.files)
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("rbac.users"))

    return render_template(
        "rbac/users.html",
        users=list_users(),
        roles=list_roles(),
        editing_user=None,
    )


@rbac_bp.route("/rbac/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    if not has_permission("rbac.manage"):
        flash("You do not have permission to manage users.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    editing_user = fetch_user_by_id(user_id)
    if not editing_user:
        flash("User not found.", "danger")
        return redirect(url_for("rbac.users"))

    if request.method == "POST":
        ok, msg = update_user(user_id, request.form, request.files)
        flash(msg, "success" if ok else "danger")
        if ok:
            if session.get("user", {}).get("id") == user_id:
                session.modified = True
            return redirect(url_for("rbac.users"))

    return render_template(
        "rbac/users.html",
        users=list_users(),
        roles=list_roles(),
        editing_user=editing_user,
    )


@rbac_bp.route("/rbac/roles", methods=["GET", "POST"])
def roles():
    if not has_permission("rbac.manage"):
        flash("You do not have permission to manage roles.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    role_key = request.args.get("role") or "ADMIN"
    role_map = get_role_map()
    if role_key not in role_map:
        role_key = "ADMIN"

    if request.method == "POST":
        role_key = request.form.get("role_key") or role_key
        permission_keys = request.form.getlist("permission_keys")
        update_role_permissions(role_key, permission_keys)
        flash("Role permissions updated successfully.", "success")
        return redirect(url_for("rbac.roles", role=role_key))

    role_permission_map = get_role_permissions_map()
    return render_template(
        "rbac/roles.html",
        roles=list_roles(),
        permissions=list_permissions(),
        role_map=role_map,
        permission_map=get_permission_map(),
        role_permission_map=role_permission_map,
        selected_role=role_key,
        selected_permissions=role_permission_map.get(role_key, set()),
    )


@rbac_bp.route("/rbac/roles/create", methods=["POST"])
def create_role_route():
    if not has_permission("rbac.manage"):
        flash("You do not have permission to manage roles.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    ok, msg = create_role(request.form)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("rbac.roles"))


@rbac_bp.route("/rbac/roles/<role_key>/update", methods=["POST"])
def update_role_route(role_key):
    if not has_permission("rbac.manage"):
        flash("You do not have permission to manage roles.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    ok, msg = update_role(role_key, request.form)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("rbac.roles", role=role_key))


@rbac_bp.route("/rbac/permissions/create", methods=["POST"])
def create_permission_route():
    if not has_permission("rbac.manage"):
        flash("You do not have permission to manage permissions.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    ok, msg = create_permission(request.form)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("rbac.roles", role=request.form.get("selected_role") or "ADMIN"))


@rbac_bp.route("/rbac/permissions/<path:permission_key>/update", methods=["POST"])
def update_permission_route(permission_key):
    if not has_permission("rbac.manage"):
        flash("You do not have permission to manage permissions.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    ok, msg = update_permission(permission_key, request.form)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("rbac.roles", role=request.form.get("selected_role") or "ADMIN"))
