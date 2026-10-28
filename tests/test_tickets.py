import sqlite3
import pytest
import app as repair_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Create a temporary database
    test_db = tmp_path / "tickets.db"

    connection = sqlite3.connect(test_db)
    
    connection.execute("""
    CREATE TABLE tickets (
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


    connection.execute("""
    CREATE TABLE quote_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_phone TEXT,
        customer_email TEXT,
        device_type TEXT NOT NULL,
        issue TEXT NOT NULL,
        damage_photo TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0
        )
    """)

    # Add one sample ticket
    connection.execute("""
        INSERT INTO tickets
        (customer_name, customer_phone, device_type, issue)
        VALUES (?, ?, ?, ?)
    """, ("Test Customer", "555-123-4567", "iPhone", "Broken Screen"))

    connection.commit()
    connection.close()

    original_connect = sqlite3.connect

    def test_connect(database, *args, **kwargs):
        if str(database) == "tickets.db":
            return original_connect(test_db, *args, **kwargs)
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(repair_app.sqlite3, "connect", test_connect)

    repair_app.app.config["TESTING"] = True

    with repair_app.app.test_client() as test_client:
        yield test_client


# Test 1: View an existing ticket
def test_view_ticket(client):
    response = client.get("/ticket/1")

    assert response.status_code == 200
    assert b"Test Customer" in response.data


# Test 2: Search for a ticket
def test_search_ticket(client):
    response = client.get("/dashboard?search=Test")

    assert response.status_code == 200
    assert b"Test Customer" in response.data
    
    
# Test 3: Edit an existing repair ticket
def test_edit_ticket(client):
    response = client.post("/ticket/1/edit", data={
        "status": "In Progress",
        "technician_notes": "Replacing screen",
        "customer_phone": "555-123-4567",
        "customer_email": "test@example.com",
        "parts_cost": "50",
        "labor_cost": "30"
    })

    assert response.status_code == 302

    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row
    ticket = connection.execute(
        "SELECT * FROM tickets WHERE id = 1"
    ).fetchone()
    connection.close()

    assert ticket["status"] == "In Progress"
    assert ticket["technician_notes"] == "Replacing screen"
    assert ticket["total_cost"] == 80


# Test 4: Create a new repair ticket
def test_create_ticket(client):
    response = client.post("/create", data={
        "customer_name": "New Customer",
        "customer_phone": "5551234567",
        "customer_email": "new@example.com",
        "device_type": "Samsung",
        "issue": "Battery Replacement",
        "technician_notes": "Needs new battery"
    })

    assert response.status_code == 302
    assert response.location.endswith("/dashboard")

    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row
    ticket = connection.execute(
        "SELECT * FROM tickets WHERE customer_name = ?",
        ("New Customer",)
    ).fetchone()
    connection.close()

    assert ticket is not None
    assert ticket["device_type"] == "Samsung"
    assert ticket["customer_phone"] == "555-123-4567"


# Test 5: Delete an existing repair ticket
def test_delete_ticket(client):
    connection = sqlite3.connect("tickets.db")
    ticket = connection.execute(
        "SELECT id FROM tickets WHERE id = 1"
    ).fetchone()
    connection.close()

    assert ticket is not None

    response = client.post("/ticket/1/delete")

    assert response.status_code == 302
    assert response.location.endswith("/dashboard")

    connection = sqlite3.connect("tickets.db")
    ticket = connection.execute(
        "SELECT id FROM tickets WHERE id = 1"
    ).fetchone()
    connection.close()

    assert ticket is None


# Test 6: View a printable repair ticket
def test_print_ticket(client):
    response = client.get("/ticket/1/print")

    assert response.status_code == 200
    assert b"Test Customer" in response.data
    assert b"Broken Screen" in response.data


# Test 7: Submit a customer quote request
def test_quote_request(client):
    response = client.post("/quote-request", data={
        "customer_name": "Quote Customer",
        "customer_phone": "5551234567",
        "customer_email": "quote@example.com",
        "device_type": "iPhone",
        "issue": "Broken Screen"
    })

    assert response.status_code == 200
    assert b"Quote Request Submitted!" in response.data

    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row

    quote = connection.execute(
        "SELECT * FROM quote_requests WHERE customer_name = ?",
        ("Quote Customer",)
    ).fetchone()

    connection.close()

    assert quote is not None
    assert quote["customer_name"] == "Quote Customer"
    
    
# Test 8: Check customer repair status
def test_status_lookup(client):
    response = client.post("/status-lookup", data={
        "ticket_id": "1",
        "customer_phone": "5551234567"
    })

    assert response.status_code == 200
    assert b"Test Customer" in response.data


# Test 9: View customer quote details
def test_quote_detail(client):
    connection = sqlite3.connect("tickets.db")
    connection.execute("""
        INSERT INTO quote_requests (
            customer_name, customer_phone,
            customer_email, device_type, issue
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        "Quote Customer", "555-123-4567",
        "quote@example.com", "iPhone", "Broken Screen"
    ))
    quote_id = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]
    connection.commit()
    connection.close()

    response = client.get(f"/quote/{quote_id}")

    assert response.status_code == 200
    assert b"Quote Customer" in response.data

