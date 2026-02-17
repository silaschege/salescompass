import sqlite3
import os

db_path = 'db.sqlite3'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
    indexes = cur.fetchall()
    print("Found following indexes:")
    for idx in indexes:
        if '0888f9df' in idx[0] or 'billing' in idx[0]:
            print(idx)
    conn.close()
