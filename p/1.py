import psycopg2
import csv
import re
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

# --- Connection ---

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

# --- Table setup ---

def create_table():
    command = """CREATE TABLE IF NOT EXISTS contacts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(20) NOT NULL
            )"""
    with conn.cursor() as cur:
        cur.execute(command)
        conn.commit()

# --- INSERT ---

def insert_contact(name, phone):
    command = "INSERT INTO contacts(name, phone) VALUES(%s, %s)"
    with conn.cursor() as cur:
        cur.execute(command, (name, phone))
        conn.commit()

def insert_from_console():
    name = input("Enter name: ")
    phone = input("Enter phone: ")
    insert_contact(name, phone)
    print(f"Added: {name} - {phone}")

def insert_from_csv(csv_file):
    command = "INSERT INTO contacts(name, phone) VALUES(%s, %s)"
    with conn.cursor() as cur:
        with open(csv_file, "r") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                name, phone = row
                cur.execute(command, (name, phone))
        conn.commit()
    print(f"Imported contacts from {csv_file}")

# --- SELECT ---

def get_all_contacts():
    command = "SELECT * FROM contacts ORDER BY name"
    with conn.cursor() as cur:
        cur.execute(command)
        return cur.fetchall()

def search_contacts(pattern):
    command = "SELECT * FROM contacts WHERE name ILIKE %s OR phone ILIKE %s"
    like_pattern = f"%{pattern}%"
    with conn.cursor() as cur:
        cur.execute(command, (like_pattern, like_pattern))
        return cur.fetchall()

# --- UPDATE ---

def update_phone(name, new_phone):
    command = "UPDATE contacts SET phone = %s WHERE name = %s"
    with conn.cursor() as cur:
        cur.execute(command, (new_phone, name))
        conn.commit()
        print(f"Updated {cur.rowcount} row(s)")

def update_name(phone, new_name):
    command = "UPDATE contacts SET name = %s WHERE phone = %s"
    with conn.cursor() as cur:
        cur.execute(command, (new_name, phone))
        conn.commit()
        print(f"Updated {cur.rowcount} row(s)")

# --- DELETE ---

def delete_by_name(name):
    command = "DELETE FROM contacts WHERE name = %s"
    with conn.cursor() as cur:
        cur.execute(command, (name,))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")

def delete_by_phone(phone):
    command = "DELETE FROM contacts WHERE phone = %s"
    with conn.cursor() as cur:
        cur.execute(command, (phone,))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")


# ============================================================
# NEW FUNCTIONS
# ============================================================

# 1. Search contacts by pattern (name, surname, or phone fragment)
def search_by_pattern(pattern):
    """
    Returns all records where the name OR phone contains the given pattern.
    Matches partial names, surnames, and phone numbers (case-insensitive).
    """
    command = """
        SELECT * FROM contacts
        WHERE name ILIKE %s OR phone ILIKE %s
        ORDER BY name
    """
    like_pattern = f"%{pattern}%"
    with conn.cursor() as cur:
        cur.execute(command, (like_pattern, like_pattern))
        return cur.fetchall()


# 2. Upsert: insert a new contact, or update phone if name already exists
def upsert_contact(name, phone):
    """
    Inserts a new contact by name and phone.
    If a contact with the same name already exists, updates their phone instead.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
        existing = cur.fetchone()
        if existing:
            cur.execute("UPDATE contacts SET phone = %s WHERE name = %s", (phone, name))
        else:
            cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (name, phone))
        conn.commit()
    print(f"Upserted: {name} - {phone}")


# 3. Bulk insert from a list; validate phone format, return invalid entries
def insert_many_contacts(contacts_list):
    """
    Inserts many contacts from a list of (name, phone) tuples.
    Validates each phone number: must contain only digits, spaces, +, -, (, ).
    Skips invalid entries, prints them, and returns them as a list.

    Args:
        contacts_list: list of (name, phone) tuples

    Returns:
        list of (name, phone) tuples that failed validation
    """
    phone_pattern = re.compile(r'^[\d\s\+\-\(\)]+$')
    invalid_entries = []

    with conn.cursor() as cur:
        for name, phone in contacts_list:
            # Validate: name must not be empty, phone must match pattern
            if not name or not name.strip():
                print(f"  [INVALID] Empty name for phone '{phone}' — skipped")
                invalid_entries.append((name, phone))
                continue

            if not phone_pattern.match(phone.strip()):
                print(f"  [INVALID] Bad phone '{phone}' for '{name}' — skipped")
                invalid_entries.append((name, phone))
                continue

            # Check if name already exists, then insert or update
            cur.execute("SELECT id FROM contacts WHERE name = %s", (name.strip(),))
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE contacts SET phone = %s WHERE name = %s",
                    (phone.strip(), name.strip())
                )
            else:
                cur.execute(
                    "INSERT INTO contacts (name, phone) VALUES (%s, %s)",
                    (name.strip(), phone.strip())
                )

        conn.commit()

    valid_count = len(contacts_list) - len(invalid_entries)
    print(f"\nInserted/updated {valid_count} contact(s). "
          f"{len(invalid_entries)} invalid entry/entries skipped.")

    return invalid_entries


# 4. Paginated fetch: return contacts page by page using LIMIT / OFFSET
def get_contacts_paginated(page=1, page_size=10):
    """
    Returns a single page of contacts ordered by name.

    Args:
        page:      1-based page number (default 1)
        page_size: number of records per page (default 10)

    Returns:
        tuple (rows, total_count)
            rows        — list of contact tuples for this page
            total_count — total number of contacts in the table
    """
    offset = (page - 1) * page_size

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM contacts")
        total_count = cur.fetchone()[0]

        cur.execute(
            "SELECT * FROM contacts ORDER BY name LIMIT %s OFFSET %s",
            (page_size, offset)
        )
        rows = cur.fetchall()

    return rows, total_count


# 5. Delete by username OR phone (single procedure handles both cases)
def delete_by_name_or_phone(identifier):
    """
    Deletes contact(s) where name OR phone matches the identifier exactly.
    A single call handles both use-cases so callers don't need to know
    whether they have a name or a phone number.
    """
    command = "DELETE FROM contacts WHERE name = %s OR phone = %s"
    with conn.cursor() as cur:
        cur.execute(command, (identifier, identifier))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s) matching '{identifier}'")


# ============================================================
# Main menu
# ============================================================

def print_contacts(contacts):
    if not contacts:
        print("  (no contacts)")
        return
    for c in contacts:
        print(f"  [{c[0]}] {c[1]} - {c[2]}")


def main():
    create_table()

    while True:
        print("\n--- PhoneBook ---")
        print("1.  Show all contacts")
        print("2.  Add contact (console)")
        print("3.  Import from CSV")
        print("4.  Search (original)")
        print("5.  Update phone by name")
        print("6.  Update name by phone")
        print("7.  Delete by name")
        print("8.  Delete by phone")
        print("--- New features ---")
        print("9.  Search by pattern (name / surname / phone fragment)")
        print("10. Upsert contact (insert or update phone)")
        print("11. Bulk insert with validation")
        print("12. Browse contacts with pagination")
        print("13. Delete by name OR phone")
        print("0.  Exit")

        choice = input("\nChoice: ")

        if choice == "1":
            print_contacts(get_all_contacts())

        elif choice == "2":
            insert_from_console()

        elif choice == "3":
            filename = input("CSV file path: ")
            insert_from_csv(filename)

        elif choice == "4":
            pattern = input("Search: ")
            print_contacts(search_contacts(pattern))

        elif choice == "5":
            name = input("Name: ")
            new_phone = input("New phone: ")
            update_phone(name, new_phone)

        elif choice == "6":
            phone = input("Phone: ")
            new_name = input("New name: ")
            update_name(phone, new_name)

        elif choice == "7":
            name = input("Name: ")
            delete_by_name(name)

        elif choice == "8":
            phone = input("Phone: ")
            delete_by_phone(phone)

        # --- New features ---

        elif choice == "9":
            pattern = input("Enter pattern (name, surname, or phone fragment): ")
            results = search_by_pattern(pattern)
            print_contacts(results)

        elif choice == "10":
            name = input("Name: ")
            phone = input("Phone: ")
            upsert_contact(name, phone)

        elif choice == "11":
            print("Enter contacts as 'Name,Phone' lines. Empty line to finish.")
            entries = []
            while True:
                line = input("  > ").strip()
                if not line:
                    break
                parts = line.split(",", 1)
                if len(parts) == 2:
                    entries.append((parts[0].strip(), parts[1].strip()))
                else:
                    print("  Format must be: Name,Phone")
            invalid = insert_many_contacts(entries)
            if invalid:
                print("\nInvalid entries returned:")
                for name, phone in invalid:
                    print(f"  Name='{name}', Phone='{phone}'")

        elif choice == "12":
            page_size = int(input("Records per page [10]: ").strip() or "10")
            page = 1
            while True:
                rows, total = get_contacts_paginated(page, page_size)
                total_pages = max(1, -(-total // page_size))  # ceiling division
                print(f"\n  Page {page}/{total_pages}  (total: {total} contacts)")
                print_contacts(rows)
                nav = input("  [n]ext / [p]rev / [q]uit: ").strip().lower()
                if nav == "n" and page < total_pages:
                    page += 1
                elif nav == "p" and page > 1:
                    page -= 1
                elif nav == "q":
                    break

        elif choice == "13":
            identifier = input("Enter name or phone to delete: ")
            delete_by_name_or_phone(identifier)

        elif choice == "0":
            break

        else:
            print("Invalid choice")

    conn.close()
    print("Goodbye!")


if __name__ == "__main__":
    main()