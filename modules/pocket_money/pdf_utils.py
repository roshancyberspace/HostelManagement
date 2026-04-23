from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from models.db import get_db
import datetime

def generate_monthly_pocket_pdf(ledger_no, year, month, file_path):
    db = get_db()

    txns = db.execute("""
        SELECT *
        FROM pocket_money_transactions
        WHERE ledger_no = ?
        AND strftime('%Y', created_at) = ?
        AND strftime('%m', created_at) = ?
        ORDER BY created_at
    """, (ledger_no, str(year), f"{int(month):02d}")).fetchall()

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Pocket Money Monthly Statement")

    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Ledger No: {ledger_no}")
    c.drawString(300, y, f"Month: {month}/{year}")

    y -= 30
    c.drawString(50, y, "Date")
    c.drawString(120, y, "Type")
    c.drawString(200, y, "Category")
    c.drawString(300, y, "Amount")

    y -= 15
    c.line(50, y, 550, y)
    y -= 15

    for t in txns:
        if y < 50:
            c.showPage()
            y = height - 50

        c.drawString(50, y, t["created_at"][:10])
        c.drawString(120, y, t["txn_type"])
        c.drawString(200, y, t["category"] or "-")
        c.drawString(300, y, f"₹ {t['amount']}")
        y -= 15

    c.save()
