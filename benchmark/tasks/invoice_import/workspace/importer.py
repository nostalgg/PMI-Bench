"""Import CSV invoices into the existing SQLite database (intentionally buggy)."""
import csv
import sqlite3


def import_invoices(csv_path, db_path):
    count = 0
    with open(csv_path, newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        with sqlite3.connect(db_path) as connection:
            for row in reader:
                connection.execute(
                    "INSERT INTO invoices VALUES (?, ?, ?, ?)",
                    (row["invoice_id"], row["customer_id"],
                     int(row["amount_cents"]), row["status"]),
                )
                connection.commit()
                count += 1
    return count
