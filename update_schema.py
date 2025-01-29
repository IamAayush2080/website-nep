import sqlite3

def add_balance_column():
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    
    # Check if the 'balance' column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'balance' not in columns:
        # Add the 'balance' column with a default value of 0.0
        cursor.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
        print("Column 'balance' added successfully.")
    else:
        print("Column 'balance' already exists.")
    
    conn.commit()
    conn.close()

add_balance_column()
