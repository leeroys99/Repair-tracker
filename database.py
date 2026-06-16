import sqlite3

connection = sqlite3.connect("tickets.db")

cursor = connection.cursor()


#CREATE TICKET REQUEST#
cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_email TEXT,
    device_type TEXT NOT NULL,
    issue TEXT NOT NULL,
    technician_notes TEXT,
    status TEXT DEFAULT 'Needs Diagnostics',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    parts_cost REAL DEFAULT 0,
    labor_cost REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    damage_photo TEXT
)
""")


#CUSTOMER QUOTE/TICKET REQUEST#
cursor.execute("""
CREATE TABLE IF NOT EXISTS quote_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_email TEXT,
    device_type TEXT NOT NULL,
    issue TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'New Request',
    damage_photo TEXT
)
""")


#INVENTORY TABLE#
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 0
)
""")

connection.commit()
connection.close()

print("Database created successfully!")