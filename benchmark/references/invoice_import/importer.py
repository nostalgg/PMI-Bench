"""Reference solution, not the only accepted implementation."""
import csv
import sqlite3


def import_invoices(csv_path, db_path):
    fields = {"invoice_id", "customer_id", "amount_cents", "status"}
    invoices = {}
    with open(csv_path, newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if not fields.issubset(reader.fieldnames or []):
            raise ValueError("Missing required CSV headers")
        for row in reader:
            if any(row.get(field) is None for field in fields):
                raise ValueError("Missing required value")
            invoice_id = row["invoice_id"].strip()
            customer_id = row["customer_id"].strip()
            amount = row["amount_cents"].strip()
            status = row["status"].strip()
            if not invoice_id or not customer_id:
                raise ValueError("Empty identifier")
            if not amount or any(char not in "0123456789" for char in amount):
                raise ValueError("Invalid cents")
            cents = int(amount)
            if cents > 2**63 - 1:
                raise ValueError("Cents exceed SQLite integer range")
            if status not in {"issued", "paid", "cancelled"}:
                raise ValueError("Invalid invoice status")
            invoices[invoice_id] = (invoice_id, customer_id, cents, status)
    with sqlite3.connect(db_path) as connection:
        connection.executemany(
            """INSERT INTO invoices (invoice_id, customer_id, amount_cents, status)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(invoice_id) DO UPDATE SET
                   customer_id=excluded.customer_id,
                   amount_cents=excluded.amount_cents,
                   status=excluded.status""",
            invoices.values(),
        )
    return len(invoices)
