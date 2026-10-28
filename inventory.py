
import sqlite3


# Get all inventory items
def get_inventory():
    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row
    items = connection.execute("SELECT * FROM inventory").fetchall()
    connection.close()
    return items


# Add a new inventory item
def add_item(item_name, quantity):
    connection = sqlite3.connect("tickets.db")
    connection.execute(
        "INSERT INTO inventory (item_name, quantity) VALUES (?, ?)",
        (item_name, quantity)
    )
    connection.commit()
    connection.close()


# Update an item's quantity
def update_item(item_id, quantity):
    connection = sqlite3.connect("tickets.db")
    connection.execute(
        "UPDATE inventory SET quantity = ? WHERE id = ?",
        (quantity, item_id)
    )
    connection.commit()
    connection.close()


# Delete an inventory item
def delete_item(item_id):
    connection = sqlite3.connect("tickets.db")
    connection.execute(
        "DELETE FROM inventory WHERE id = ?",
        (item_id,)
    )
    connection.commit()
    connection.close()


# Check if an inventory quantity is valid
def validate_quantity(quantity):
    return quantity >= 0
