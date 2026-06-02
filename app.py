from flask import Flask, render_template, request, redirect
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

print("Current Folder:", os.getcwd())

@app.route("/")
def home():
    return render_template("index.html")


#SEARCHTICKET#


@app.route("/dashboard")
def dashboard():
    search = request.args.get("search", "")

    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if search:
        cursor.execute("""
        SELECT * FROM tickets
        WHERE customer_name LIKE ?
        OR device_type LIKE ?
        OR status LIKE ?
        """, (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ))
    else:
        cursor.execute("SELECT * FROM tickets")

    tickets = cursor.fetchall()
    
    cursor.execute("SELECT * FROM quote_requests ORDER BY id DESC")
    quote_requests = cursor.fetchall()
    
    connection.close()

    return render_template("dashboard.html", tickets=tickets, quote_requests=quote_requests, search=search)


	#TICKETTABLE#


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        customer_name = request.form["customer_name"]
        customer_phone = request.form["customer_phone"]
        customer_email = request.form["customer_email"]
        
        print("Before:", customer_phone)
        
        customer_phone = customer_phone.replace("-", "").replace(" ", "")
        
        if len (customer_phone) == 10 and customer_phone.isdigit():
            customer_phone = f"{customer_phone[:3]}-{customer_phone[3:6]}-{customer_phone[6:]}"
        
        print("After:", customer_phone)

        
        device_type = request.form["device_type"]
        issue = request.form["issue"]
        technician_notes = request.form["technician_notes"]

        connection = sqlite3.connect("tickets.db")
        cursor = connection.cursor()

        created_at = datetime.now().strftime("%m/%d/%Y %I:%M %p")

        cursor.execute("""
        INSERT INTO tickets (
            customer_name,
            customer_phone,
            customer_email,
            device_type,
            issue,
            technician_notes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_name,
            customer_phone,
            customer_email,
            device_type,
            issue,
            technician_notes,
            created_at
        ))

        connection.commit()
        connection.close()

        return redirect("/dashboard")

    return render_template("create.html")


#TICKETID#


@app.route("/ticket/<int:ticket_id>")
def ticket_detail(ticket_id):
	connection = sqlite3.connect("tickets.db")
	connection.row_factory = sqlite3.Row

	cursor = connection.cursor()

	cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
	ticket = cursor.fetchone()

	connection.close()

	return render_template("ticket.html", ticket=ticket)


#TECH:EDIT TICKET#


@app.route("/ticket/<int:ticket_id>/edit", methods=["GET", "POST"])
def edit_ticket(ticket_id):
    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if request.method == "POST":
        status = request.form["status"]
        technician_notes = request.form["technician_notes"]
        customer_phone = request.form["customer_phone"]
        customer_email = request.form["customer_email"]

        parts_cost = float(request.form["parts_cost"])
        labor_cost = float(request.form["labor_cost"])
        total_cost = parts_cost + labor_cost

        cursor.execute("""
        UPDATE tickets
        SET 
        	status = ?,
			customer_phone = ?,
            customer_email = ?,
            technician_notes = ?,
            parts_cost = ?,
            labor_cost = ?,
            total_cost = ?
        WHERE id = ?
        """, (
            status,
            customer_phone,
            customer_email,
            technician_notes,
            parts_cost,
            labor_cost,
            total_cost,
            ticket_id
        ))

        connection.commit()
        connection.close()

        return redirect(f"/ticket/{ticket_id}")

    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()

    connection.close()

    return render_template("edit.html", ticket=ticket)


#DELETE BUTTON#


@app.route("/ticket/<int:ticket_id>/delete", methods=["POST"])
def delete_ticket(ticket_id):
    connection = sqlite3.connect("tickets.db")
    cursor = connection.cursor()

    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))

    connection.commit()
    connection.close()

    return redirect("/dashboard")


#PRINT BUTTON#


@app.route("/ticket/<int:ticket_id>/print")
def print_ticket(ticket_id):
    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()

    connection.close()

    return render_template("print.html", ticket=ticket)


#CUSTOMER REQUEST#


@app.route("/quote-request", methods=["POST"])
def quote_request():
    customer_name = request.form["customer_name"]
    customer_phone = request.form["customer_phone"]
    customer_email = request.form["customer_email"]
    device_type = request.form["device_type"]
    issue = request.form["issue"]

    customer_phone = customer_phone.replace("-", "").replace(" ", "")

    if len(customer_phone) == 10 and customer_phone.isdigit():
        customer_phone = f"{customer_phone[:3]}-{customer_phone[3:6]}-{customer_phone[6:]}"

    connection = sqlite3.connect("tickets.db")
    cursor = connection.cursor()

    cursor.execute("""
    INSERT INTO quote_requests (
        customer_name,
        customer_phone,
        customer_email,
        device_type,
        issue
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        customer_name,
        customer_phone,
        customer_email,
        device_type,
        issue
    ))

    connection.commit()
    connection.close()

    return """
    <h1>Quote Request Submitted!</h1>
    <p>Thank you! We'll review your request and call you back with a possible quote.</p>
    <a href="/">Back to Home</a>
    """


#QUOTE TABLE#


@app.route("/quote/<int:quote_id>")
def quote_detail(quote_id):
    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM quote_requests WHERE id = ?", (quote_id,))
    quote = cursor.fetchone()

    connection.close()

    return render_template("quote.html", quote=quote)


#QUOTE TO TICKET#


@app.route("/convert-quote/<int:quote_id>", methods=["POST"])
def convert_quote(quote_id):

    connection = sqlite3.connect("tickets.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM quote_requests WHERE id = ?",(quote_id,))
    quote = cursor.fetchone()
    
    cursor.execute("""
    INSERT INTO tickets (
        customer_name,
        customer_phone,
        customer_email,
        device_type,
        issue,
        technician_notes,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        quote["customer_name"],
        quote["customer_phone"],
        quote["customer_email"],
        quote["device_type"],
        quote["issue"],
        "",
        "Needs Diagnostics"
    ))
    
    cursor.execute("DELETE FROM quote_requests WHERE id = ?", (quote_id,))

    connection.commit()
    connection.close()

    return redirect("/dashboard")


if __name__ == "__main__":
	app.run(debug=True)