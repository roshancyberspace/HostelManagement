import sqlite3

conn = sqlite3.connect("database/hostel.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

print("📋 Tables in hostel.db:")
for t in tables:
    print(" -", t[0])

conn.close()
