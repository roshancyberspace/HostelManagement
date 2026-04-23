from flask import Blueprint, render_template, request, redirect
from models.stock_model import (
    add_stock_item, get_stock_items,
    assign_stock, get_room_stock,
    get_area_stock, update_stock_status
)

stock_bp = Blueprint("stock", __name__, url_prefix="/stock")

# -------------------------
# STOCK DASHBOARD
# -------------------------
@stock_bp.route("/")
def dashboard():
    return render_template(
        "stock/stock_dashboard.html",
        items=get_stock_items()
    )

# -------------------------
# STOCK MASTER
# -------------------------
@stock_bp.route("/master", methods=["GET", "POST"])
def stock_master():
    if request.method == "POST":
        add_stock_item(
            request.form["name"],
            request.form["category"],
            request.form["unit"]
        )
        return redirect("/stock/master")

    return render_template(
        "stock/stock_master.html",
        items=get_stock_items()
    )

# -------------------------
# ROOM STOCK
# -------------------------
@stock_bp.route("/room/<int:room_id>", methods=["GET", "POST"])
def room_stock(room_id):
    if request.method == "POST":
        assign_stock(
            "ROOM",
            room_id,
            request.form["item_id"],
            request.form["qty"]
        )
        return redirect(f"/stock/room/{room_id}")

    return render_template(
        "stock/room_stock.html",
        stock=get_room_stock(room_id),
        items=get_stock_items(),
        room_id=room_id
    )

# -------------------------
# COMMON AREA STOCK
# -------------------------
@stock_bp.route("/area/<int:area_id>", methods=["GET", "POST"])
def area_stock(area_id):
    if request.method == "POST":
        assign_stock(
            "COMMON",
            area_id,
            request.form["item_id"],
            request.form["qty"]
        )
        return redirect(f"/stock/area/{area_id}")

    return render_template(
        "stock/area_stock.html",
        stock=get_area_stock(area_id),
        items=get_stock_items(),
        area_id=area_id
    )

# -------------------------
# UPDATE STATUS
# -------------------------
@stock_bp.route("/update/<int:allocation_id>/<status>")
def update_status(allocation_id, status):
    update_stock_status(allocation_id, status)
    return redirect(request.referrer)
