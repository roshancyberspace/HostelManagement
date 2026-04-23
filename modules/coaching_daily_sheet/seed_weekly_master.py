from models.db import get_db
from modules.coaching_daily_sheet.models import init_tables


def reset_existing():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM coaching_weekly_master")
    cur.execute("DELETE FROM study_duty_weekly_master")
    cur.execute("DELETE FROM coaching_daily_sheet")
    cur.execute("DELETE FROM study_duty_daily_sheet")
    conn.commit()
    conn.close()


def seed_coaching_weekly_master():
    conn = get_db()
    cur = conn.cursor()

    data = []

    # ---------------------------
    # Class I to V (Mon-Fri) 02:30-04:00
    # ---------------------------
    for cls in ["I", "II", "III", "IV", "V"]:
        teachers_mon = {"I": "MISS RIVA", "II": "MISS RIVA", "III": "MRS VARSHA",
                        "IV": "MRS VARSHA & MISS SONALI", "V": "MISS SONALI"}
        data.append(("Mon", cls, "ENGLISH", "02:30 PM", "04:00 PM", teachers_mon[cls]))

        teachers_tue = {"I": "MRS RAJNI", "II": "MRS RAJNI", "III": "MRS TRIPTI",
                        "IV": "MRS TRIPTI & MRS SIMPI", "V": "MRS SIMPI"}
        data.append(("Tue", cls, "HINDI", "02:30 PM", "04:00 PM", teachers_tue[cls]))

        teachers_wed = {"I": "MRS RUPAM", "II": "MRS RUPAM", "III": "MISS ISHIKA",
                        "IV": "MISS ISHIKA & MISS AKANSHA", "V": "MISS AKANSHA"}
        data.append(("Wed", cls, "MATH", "02:30 PM", "04:00 PM", teachers_wed[cls]))

        teachers_thu = {"I": "MISS DIPIKA", "II": "MISS DIPIKA", "III": "MISS MIRNAL",
                        "IV": "MISS MIRNAL & MISS YUKTA", "V": "MISS YUKTA"}
        data.append(("Thu", cls, "SCIENCE", "02:30 PM", "04:00 PM", teachers_thu[cls]))

        teachers_fri = {"I": "MRS NEHA", "II": "MISS RICHA", "III": "MISS ANJALI",
                        "IV": "MISS ANJALI & MRS RATNA", "V": "MRS RATNA"}
        data.append(("Fri", cls, "S.ST", "02:30 PM", "04:00 PM", teachers_fri[cls]))

    # ---------------------------
    # VI to VIII
    # ---------------------------
    data += [
        ("Mon", "VI", "ENG", "02:30 PM", "04:00 PM", "KAMINI SINGH"),
        ("Mon", "VII", "MATH", "02:30 PM", "04:00 PM", "RAUSHAN RATHORE"),
        ("Mon", "VIII", "HINDI", "02:30 PM", "04:00 PM", "RASHMI CHAVAI"),

        ("Wed", "VI", "HINDI", "02:30 PM", "04:00 PM", "RASHMI CHAVAI"),
        ("Wed", "VII", "ENG", "02:30 PM", "04:00 PM", "DEEPSHIKA ROY"),
        ("Wed", "VIII", "MATH", "02:30 PM", "04:00 PM", "ASHOK SINGH"),

        ("Fri", "VI", "MATH", "02:30 PM", "04:00 PM", "RAUSHAN RATHORE"),
        ("Fri", "VII", "HINDI", "02:30 PM", "04:00 PM", "RASHMI"),
        ("Fri", "VIII", "ENG", "02:30 PM", "04:00 PM", "KAMINI SINGH"),

        ("Sat", "VI", "ROBOTICS / STEAM", "02:30 PM", "04:00 PM", ""),
        ("Sat", "VII", "ROBOTICS / STEAM", "02:30 PM", "04:00 PM", ""),
        ("Sat", "VIII", "HINDI", "02:30 PM", "04:00 PM", "RASHMI CHAVAI"),

        ("Tue", "VI", "ROTATION (AS PER WEEK)", "02:30 PM", "04:00 PM", "AS PER WEEK"),
        ("Tue", "VII", "ROTATION (AS PER WEEK)", "02:30 PM", "04:00 PM", "AS PER WEEK"),
        ("Tue", "VIII", "ROTATION (AS PER WEEK)", "02:30 PM", "04:00 PM", "AS PER WEEK"),

        ("Thu", "VI", "ROTATION (AS PER WEEK)", "02:30 PM", "04:00 PM", "AS PER WEEK"),
        ("Thu", "VII", "ROTATION (AS PER WEEK)", "02:30 PM", "04:00 PM", "AS PER WEEK"),
        ("Thu", "VIII", "ROTATION (AS PER WEEK)", "02:30 PM", "04:00 PM", "AS PER WEEK"),
    ]

    # ---------------------------
    # CLASS IX (2:30-3:30 + 3:30-4:30)
    # ---------------------------
    data += [
        ("Mon", "IX", "GEOGRAPHY", "02:30 PM", "03:30 PM", "MS ANJALI"),
        ("Mon", "IX", "HISTORY", "03:30 PM", "04:30 PM", "MR UMESH"),

        ("Tue", "IX", "ENGLISH", "02:30 PM", "03:30 PM", "MR SOUMEN PATRA"),
        ("Tue", "IX", "CIVICS", "03:30 PM", "04:30 PM", "MS ANJALI"),

        ("Wed", "IX", "MATH", "02:30 PM", "03:30 PM", "MR MUKESH"),
        ("Wed", "IX", "BIOLOGY", "03:30 PM", "04:30 PM", "MR SANJEEV"),

        ("Thu", "IX", "HINDI", "02:30 PM", "03:30 PM", "MR BHIMSEN YADAV"),
        ("Thu", "IX", "PHYSICS", "03:30 PM", "04:30 PM", "MR D.N. CHOUDHARY"),

        ("Fri", "IX", "CHEMISTRY", "02:30 PM", "03:30 PM", "MR RANJAY"),
        ("Fri", "IX", "ECO", "03:30 PM", "04:30 PM", "MS ANJALI"),

        ("Sat", "IX", "AI", "02:30 PM", "03:30 PM", ""),
        ("Sat", "IX", "IT", "03:30 PM", "04:30 PM", ""),
    ]

    # ---------------------------
    # CLASS X (2:30-3:30 + 3:30-4:30 + 7:00-8:00)
    # ---------------------------
    data += [
        ("Mon", "X", "MATH", "02:30 PM", "03:30 PM", "MR MUKESH"),
        ("Mon", "X", "ENG", "03:30 PM", "04:30 PM", "MR SOUMEN PATRA"),
        ("Mon", "X", "PHY", "07:00 PM", "08:00 PM", "MR D N CHOUDHRY"),

        ("Tue", "X", "GEO", "02:30 PM", "03:30 PM", "MS AISHWARYA"),
        ("Tue", "X", "MATH", "03:30 PM", "04:30 PM", "MR MUKESH"),
        ("Tue", "X", "ECO", "07:00 PM", "08:00 PM", "MR RAKESH"),

        ("Wed", "X", "PHY", "02:30 PM", "03:30 PM", "MR D N CHOUDHRY"),
        ("Wed", "X", "CIV", "03:30 PM", "04:30 PM", "MR UMESH"),
        ("Wed", "X", "HINDI", "07:00 PM", "08:00 PM", "MR BHIM SEN YADAV"),

        ("Thu", "X", "HIST", "02:30 PM", "03:30 PM", "MR UMESH"),
        ("Thu", "X", "CHEM", "03:30 PM", "04:30 PM", "MR RANJAY"),
        ("Thu", "X", "BIO", "07:00 PM", "08:00 PM", "MR SANJEEV KR SINGH"),

        ("Fri", "X", "HINDI", "02:30 PM", "03:30 PM", "MR BHIM SEN YADAV"),
        ("Fri", "X", "BIO", "03:30 PM", "04:30 PM", "MR SANJEEV KR SINGH"),
        ("Fri", "X", "CHEM", "07:00 PM", "08:00 PM", "MR RANJAY"),

        ("Sat", "X", "I.T.", "02:30 PM", "03:30 PM", "MR MUKESH"),
        ("Sat", "X", "ENG", "07:00 PM", "08:00 PM", "MR SOUMEN PATRA"),
    ]

    # ---------------------------
    # CLASS XI (2:30-3:30 + 3:30-4:30)
    # ---------------------------
    data += [
        ("Mon", "XI", "ENGLISH", "02:30 PM", "03:30 PM", "MR M.K. SINGH"),
        ("Mon", "XI", "PHYSICS / ACCOUNTS / POL SC", "03:30 PM", "04:30 PM", "MR C.K. JHA / MS TANYA / MS AISHWARYA"),

        ("Tue", "XI", "FINE ARTS / MUSIC / PHY EDU", "02:30 PM", "03:30 PM", "MR R. UPADHAYAY / MR RAHUL"),
        ("Tue", "XI", "CHEMISTRY / B.ST / HISTORY", "03:30 PM", "04:30 PM", "MRS SWETA OJHA / MS TANYA / MR UMESH"),

        ("Wed", "XI", "HISTORY / MATH / B.ST / BIO", "02:30 PM", "03:30 PM", "MR UMESH / MR C.K. JHA / MS TANYA / MR ABHISHEK"),
        ("Wed", "XI", "PHYSICS / ECO", "03:30 PM", "04:30 PM", "MR C.K. JHA / MR RAKESH"),

        ("Thu", "XI", "PHYSICS / POL SC / ACC", "02:30 PM", "03:30 PM", "MR G.K. SINGH / MS AISHWARYA / MS TANYA"),
        ("Thu", "XI", "CHEMISTRY / B.ST / HISTORY", "03:30 PM", "04:30 PM", "MRS SWETA OJHA / MS TANYA / MR UMESH"),

        ("Fri", "XI", "ECO / CHEMISTRY", "02:30 PM", "03:30 PM", "MR RAKESH / MR S.N. SINGH"),
        ("Fri", "XI", "MATH / ACC / GEO", "03:30 PM", "04:30 PM", "MR M.K. SINGH / MS TANYA / MS AISHWARYA"),

        ("Sat", "XI", "HINDI", "02:30 PM", "03:30 PM", "MR BHIMSEN YADAV"),
        ("Sat", "XI", "IP", "03:30 PM", "04:30 PM", "MR MUKESH KUMAR"),
    ]

    # ---------------------------
    # CLASS XII (2:30-3:30 + 3:30-4:30 + 7:00-8:00)
    # ---------------------------
    data += [
        ("Mon", "XII", "PHY / ACC / GEO", "02:30 PM", "03:30 PM", "MR G.K. SINGH / MS TANYA / MS AISHWARYA"),
        ("Mon", "XII", "I.P / HINDI", "03:30 PM", "04:30 PM", "MR MUKESH / MR BHIM SEN YADAV"),
        ("Mon", "XII", "SUPERVISION CLASS", "07:00 PM", "08:00 PM", "MR S.K. PANDEY (PHYSICS)"),

        ("Tue", "XII", "CHEM / B.ST / HIST", "02:30 PM", "03:30 PM", "MR S.N. SINGH / MS TANYA / MR UMESH KR SINGH"),
        ("Tue", "XII", "ENG", "03:30 PM", "04:30 PM", "MR M.K. SINGH"),
        ("Tue", "XII", "SUPERVISION CLASS", "07:00 PM", "08:00 PM", "MR G.K. SINGH (PHYSICS)"),

        ("Wed", "XII", "MATH / BIO / ECO", "02:30 PM", "03:30 PM", "MR M.K. SINGH / MR ABHISHEK PANDEY / MR RAKESH"),
        ("Wed", "XII", "PHY / ACC / GEO", "03:30 PM", "04:30 PM", "MR G.K. SINGH / MS TANYA / MS AISHWARYA"),
        ("Wed", "XII", "SUPERVISION CLASS", "07:00 PM", "08:00 PM", "MR S.N. SINGH (CHEMISTRY)"),

        ("Thu", "XII", "I.P / HINDI", "02:30 PM", "03:30 PM", "MR MUKESH / MR BHIM SEN YADAV"),
        ("Thu", "XII", "CHEM / B.ST / POL SC", "03:30 PM", "04:30 PM", "MR S.N. SINGH / MS TANYA / MS AISHWARYA"),
        ("Thu", "XII", "SUPERVISION CLASS", "07:00 PM", "08:00 PM", "MR M.K. SINGH (MATHS)"),

        ("Fri", "XII", "ENG", "02:30 PM", "03:30 PM", "MR M.K. SINGH"),
        ("Fri", "XII", "MATH / BIO / ECO", "03:30 PM", "04:30 PM", "MR M.K. SINGH / MR ABHISHEK PANDEY / MR RAKESH"),
        ("Fri", "XII", "SUPERVISION CLASS", "07:00 PM", "08:00 PM", "MISS AISHWARYA (GEO + POL SC)"),

        ("Sat", "XII", "ADDITIONAL", "02:30 PM", "03:30 PM", ""),
        ("Sat", "XII", "ADDITIONAL", "03:30 PM", "04:30 PM", ""),
    ]

    for row in data:
        cur.execute("""
            INSERT INTO coaching_weekly_master (day_name, class_name, subject, start_time, end_time, teacher_name, status)
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
        """, row)

    conn.commit()
    conn.close()


def seed_study_duty_weekly_master():
    conn = get_db()
    cur = conn.cursor()

    # Default template: editable daily
    base_rows = [
        ("I - V", "Hostel 2nd Floor Hall", "Teacher 1"),
        ("VI", "Hostel 1st Floor Hall", "Teacher 2"),
        ("VII", "Hostel 1st Floor Hall", "Teacher 2"),
        ("VIII", "Hostel 1st Floor Hall", "Teacher 2"),
        ("IX", "Hostel 2nd Floor Hall", "Teacher 3"),
        ("X", "Hostel 2nd Floor Hall", "Teacher 4"),
        ("XI", "Hostel 3rd Floor Hall", "Teacher 5"),
        ("XII", "Hostel 3rd Floor Hall", "Teacher 5"),
    ]

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for d in days:
        for cls_group, place, teacher in base_rows:
            cur.execute("""
                INSERT INTO study_duty_weekly_master
                (day_name, class_group, floor_place, teacher_name, start_time, end_time, status)
                VALUES (?, ?, ?, ?, '07:00 PM', '08:30 PM', 'ACTIVE')
            """, (d, cls_group, place, teacher))

    conn.commit()
    conn.close()


def run_seed():
    init_tables()
    reset_existing()
    seed_coaching_weekly_master()
    seed_study_duty_weekly_master()
    print("✅ SEED DONE: Weekly Master Coaching + Study Duty")


if __name__ == "__main__":
    run_seed()
