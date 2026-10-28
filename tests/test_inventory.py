import sqlite3
import pytest
import app as repair_app
import inventory as inventory_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Create a separate database for testing
    test_db = tmp_path / "tickets.db"

    connection = sqlite3.connect(test_db)
    connection.execute("""
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0
        )
    """)
    connection.commit()
    connection.close()

    # Redirect database connections to our test database
    original_connect = sqlite3.connect

    def test_connect(database, *args, **kwargs):
        if str(database) == "tickets.db":
            return original_connect(test_db, *args, **kwargs)
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(inventory_db.sqlite3, "connect", test_connect)

    repair_app.app.config["TESTING"] = True

    with repair_app.app.test_client() as test_client:
        yield test_client


# Test 1: Add an item and verify it was saved
def test_add_item(client):
    response = client.post("/add-inventory", data={
        "item_name": "iPhone Screen",
        "quantity": "5"
    })

    assert response.status_code == 302

    items = inventory_db.get_inventory()
    assert len(items) == 1
    assert items[0]["item_name"] == "iPhone Screen"
    assert items[0]["quantity"] == 5



# Test 2: Add an item with zero quantity
def test_add_zero_quantity(client):
    response = client.post("/add-inventory", data={
        "item_name": "Battery",
        "quantity": "0"
    })
    assert response.status_code == 302


# Test 3: Add an item with a large quantity
def test_add_large_quantity(client):
    response = client.post("/add-inventory", data={
        "item_name": "Charging Cable",
        "quantity": "1000"
    })
    assert response.status_code == 302


# Test 4: Add an item with a negative quantity
def test_add_negative_quantity(client):
    response = client.post("/add-inventory", data={
        "item_name": "Screen Protector",
        "quantity": "-1"
    })
    assert response.status_code == 302


# Test 5: Reject an invalid quantity
def test_add_invalid_quantity(client):
    with pytest.raises(ValueError):
        client.post("/add-inventory", data={
            "item_name": "Battery",
            "quantity": "abc"
        })



# Test 6: Update an item's quantity
def test_update_quantity(client):
    client.post("/add-inventory", data={
        "item_name": "Battery",
        "quantity": "5"
    })

    items = inventory_db.get_inventory()
    item_id = items[0]["id"]

    response = client.post(f"/update-inventory/{item_id}", data={
        "quantity": "10"
    })

    assert response.status_code == 302

    updated_items = inventory_db.get_inventory()
    assert updated_items[0]["quantity"] == 10



# Test 7: Update quantity to zero
def test_update_zero_quantity(client):
    response = client.post("/update-inventory/1", data={
        "quantity": "0"
    })
    assert response.status_code == 302


# Test 8: Update quantity to a large number
def test_update_large_quantity(client):
    response = client.post("/update-inventory/1", data={
        "quantity": "5000"
    })
    assert response.status_code == 302


# Test 9: Update quantity to a negative number
def test_update_negative_quantity(client):
    response = client.post("/update-inventory/1", data={
        "quantity": "-5"
    })
    assert response.status_code == 302


# Test 10: Reject invalid quantity when updating
def test_update_invalid_quantity(client):
    with pytest.raises(ValueError):
        client.post("/update-inventory/1", data={
            "quantity": "invalid"
        })



# Test 11: Delete an inventory item
def test_delete_item(client):
    client.post("/add-inventory", data={
        "item_name": "Battery",
        "quantity": "5"
    })

    items = inventory_db.get_inventory()
    item_id = items[0]["id"]

    response = client.post(f"/delete-inventory/{item_id}")

    assert response.status_code == 302

    remaining_items = inventory_db.get_inventory()
    assert len(remaining_items) == 0



# Test 12: Delete an item that does not exist
def test_delete_missing_item(client):
    response = client.post("/delete-inventory/999")
    assert response.status_code == 302


# Test 13: View an empty inventory
def test_view_empty_inventory(client):
    response = client.get("/inventory")
    assert response.status_code == 200


# Test 14: View inventory with an item
def test_view_inventory_with_item(client):
    client.post("/add-inventory", data={
        "item_name": "iPhone Screen",
        "quantity": "3"
    })
    response = client.get("/inventory")
    assert response.status_code == 200
    assert b"iPhone Screen" in response.data


# Test 15: Reject a missing quantity
def test_add_missing_quantity(client):
    response = client.post("/add-inventory", data={
        "item_name": "Battery"
    })
    assert response.status_code == 400


# Part B: Test inventory quantity validation
def test_validate_quantity():
    assert inventory_db.validate_quantity(5) is True
    assert inventory_db.validate_quantity(0) is True
    assert inventory_db.validate_quantity(-1) is False
