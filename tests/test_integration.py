
import sqlite3
import pytest
import app as repair_app


# Create a temporary database for each test
@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "tickets.db"
    original_connect = sqlite3.connect

    connection = original_connect(test_db)
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
    connection.commit()
    connection.close()

    # Redirect database access to the temporary database
    def test_connect(database, *args, **kwargs):
        if str(database) == "tickets.db":
            return original_connect(test_db, *args, **kwargs)
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(repair_app.sqlite3, "connect", test_connect)
    repair_app.app.config["TESTING"] = True

    with repair_app.app.test_client() as test_client:
        yield test_client


# Helper function to create a sample ticket
def create_sample_ticket(client):
    return client.post("/create", data={
        "customer_name": "Test Customer",
        "customer_phone": "5551234567",
        "customer_email": "test@example.com",
        "device_type": "iPhone",
        "issue": "Broken Screen",
        "technician_notes": "Needs repair"
    })


# Test 1: Create a ticket and verify it was saved
def test_create_ticket_integration(client):
    response = create_sample_ticket(client)

    assert response.status_code == 302

    connection = sqlite3.connect("tickets.db")
    ticket = connection.execute(
        "SELECT customer_name, device_type FROM tickets"
    ).fetchone()
    connection.close()

    assert ticket is not None
    assert ticket[0] == "Test Customer"
    assert ticket[1] == "iPhone"


# Test 2: Create and edit a ticket
def test_edit_ticket_integration(client):
    create_sample_ticket(client)

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
    ticket = connection.execute(
        "SELECT status, total_cost FROM tickets WHERE id = 1"
    ).fetchone()
    connection.close()

    assert ticket is not None
    assert ticket[0] == "In Progress"
    assert ticket[1] == 80


# Test 3: Create and delete a ticket
def test_delete_ticket_integration(client):
    create_sample_ticket(client)

    response = client.post("/ticket/1/delete")

    assert response.status_code == 302

    connection = sqlite3.connect("tickets.db")
    ticket = connection.execute(
        "SELECT id FROM tickets WHERE id = 1"
    ).fetchone()
    connection.close()

    assert ticket is None
