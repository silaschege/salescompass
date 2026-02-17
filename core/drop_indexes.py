import sqlite3
import os

db_path = 'db.sqlite3'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Find all indexes starting with billing_ that belong to invoicing_ tables
    cur.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name LIKE 'billing_%' AND tbl_name LIKE 'invoicing_%'")
    to_drop = cur.fetchall()
    
    print(f"Found {len(to_drop)} indexes to drop:")
    for name, table in to_drop:
        print(f"Dropping index {name} on table {table}")
        try:
            cur.execute(f"DROP INDEX \"{name}\"")
        except Exception as e:
            print(f"Error dropping index {name}: {e}")
            
    conn.commit()
    conn.close()
    print("Done.")
