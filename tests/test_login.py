
import sqlite3
import pytest
import app as repair_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Create a temporary database
    test_db = tmp_path / "tickets.db"

    connection = sqlite3.connect(test_db)
    connection.execute("""
        CREATE TABLE technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'tech'
        )
    """)

    # Add a test technician account
    connection.execute(
        "INSERT INTO technicians (username, password, role) VALUES (?, ?, ?)",
        ("testuser", "password123", "tech")
    )
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


# Test 1: Successful login
def test_valid_login(client):
    response = client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    assert response.status_code == 302
    assert response.location.endswith("/tickets")


# Test 2: Invalid password
def test_invalid_login(client):
    response = client.post("/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    })

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


# Test 3: Redirect users who are not logged in
def test_tickets_requires_login(client):
    response = client.get("/tickets")

    assert response.status_code == 302
    assert response.location.endswith("/login")


# Test 4: Logout clears the session
def test_logout(client):
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.location.endswith("/login")

    with client.session_transaction() as session:
        assert "logged_in" not in session
