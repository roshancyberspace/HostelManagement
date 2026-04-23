from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime


def _draw_header(c, title, date_str, day_name):
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(10.5 * cm, 28.8 * cm, title)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, 28.0 * cm, f"DATE:-  {datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%b-%Y')}")
    c.drawString(14 * cm, 28.0 * cm, f"DAY:-  {day_name}")


def _draw_table(c, x, y, col_widths, row_height, headers, rows):
    c.setFont("Helvetica-Bold", 9)
    current_x = x
    for i, h in enumerate(headers):
        c.rect(current_x, y - row_height, col_widths[i], row_height, stroke=1, fill=0)
        c.drawCentredString(current_x + col_widths[i] / 2, y - row_height + 0.25 * cm, h)
        current_x += col_widths[i]

    c.setFont("Helvetica", 9)
    row_y = y - row_height
    for r in rows:
        row_y -= row_height
        current_x = x
        for i, val in enumerate(r):
            c.rect(current_x, row_y, col_widths[i], row_height, stroke=1, fill=0)
            txt = str(val)[:70]
            c.drawString(current_x + 0.15 * cm, row_y + 0.25 * cm, txt)
            current_x += col_widths[i]

    return row_y


def generate_coaching_pdf(filepath, date_str, day_name, coaching_rows):
    """
    COACHING ONLY PDF
    """
    c = canvas.Canvas(filepath, pagesize=A4)

    _draw_header(c, "ASPCS HOSTEL COACHING DAILY SHEET", date_str, day_name)

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(10.5 * cm, 26.8 * cm, "COACHING ROUTINE")

    headers = ["CLASS", "SUBJECT", "TIMING", "TEACHER & SIGN", "REMARK"]
    col_widths = [2.2 * cm, 5.0 * cm, 3.8 * cm, 6.0 * cm, 3.0 * cm]

    table_rows = []
    for r in coaching_rows:
        timing = f"{r['start_time']} - {r['end_time']}"
        remark = r.get("remark", "")
        if r.get("status") == "SUSPENDED" and remark == "":
            remark = "SUSPENDED"
        table_rows.append([r["class_name"], r["subject"], timing, r["teacher_name"], remark])

    _draw_table(c, 1.3 * cm, 26.3 * cm, col_widths, 0.75 * cm, headers, table_rows)

    c.setFont("Helvetica", 8)
    c.drawString(1.3 * cm, 1.0 * cm, "NOTE: If coaching suspended / changed → Remark is mandatory.")

    c.showPage()
    c.save()


def generate_self_study_pdf(filepath, date_str, day_name, study_rows):
    """
    SELF STUDY ONLY PDF
    """
    c = canvas.Canvas(filepath, pagesize=A4)

    _draw_header(c, "ASPCS HOSTEL SELF STUDY DAILY SHEET", date_str, day_name)

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(10.5 * cm, 26.8 * cm, "EVENING SELF STUDY DUTY")

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(10.5 * cm, 26.3 * cm, "(Fixed Timing: 07:00 PM – 08:30 PM Daily)")

    headers = ["CLASS", "FLOOR / PLACE", "TEACHER", "SIGN & TIMING", "REMARK"]
    col_widths = [2.2 * cm, 5.0 * cm, 5.0 * cm, 4.0 * cm, 2.8 * cm]

    table_rows = []
    for r in study_rows:
        timing = f"{r['start_time']} - {r['end_time']}"
        remark = r.get("remark", "")
        if r.get("status") == "SUSPENDED" and remark == "":
            remark = "SUSPENDED"
        table_rows.append([r["class_group"], r["floor_place"], r["teacher_name"], timing, remark])

    _draw_table(c, 1.3 * cm, 25.5 * cm, col_widths, 0.75 * cm, headers, table_rows)

    c.setFont("Helvetica", 8)
    c.drawString(1.3 * cm, 1.0 * cm, "NOTE: If duty suspended / changed → Remark is mandatory.")

    c.showPage()
    c.save()
