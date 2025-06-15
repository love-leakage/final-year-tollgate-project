import sqlite3

def create_tables():
    conn = sqlite3.connect("tollgate.db")
    cursor = conn.cursor()

    # 1. Log Entry Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT NOT NULL,
            status TEXT NOT NULL,          -- "Allowed" or "Stolen"
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Not Match Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS not_match (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid_number TEXT NOT NULL,
            extracted_number TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Stolen Vehicles Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stolen_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("All tables created successfully in tollgate.db")

if __name__ == "__main__":
    create_tables()
