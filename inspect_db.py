import sqlite3

import pandas as pd

# Connect to the database
db_path = "checkpoints.db"

try:
    conn = sqlite3.connect(db_path)

    # 1. Check what tables exist
    print("--- 📂 TABLES FOUND ---")
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    print(tables)
    print("\n")

    # 2. Look at the 'checkpoints' table (Where the magic happens)
    # We select specific columns because the 'checkpoint' column is a big binary blob
    print("--- 🕵️ RECENT CHECKPOINTS (Last 5) ---")
    query = """
    SELECT thread_id, checkpoint_id, parent_checkpoint_id 
    FROM checkpoints 
    ORDER BY checkpoint_id DESC 
    LIMIT 5
    """
    df = pd.read_sql(query, conn)
    print(df.to_string(index=False))

    conn.close()

except Exception as e:
    print(f"Error: {e}")
    print("Make sure the file 'checkpoints.db' exists in this folder!")
