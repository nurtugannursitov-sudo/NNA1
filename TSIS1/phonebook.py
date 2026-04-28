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

VALID_PHONE_TYPES = ("home", "work", "mobile")
VALID_GROUPS      = ("Family", "Work", "Friend", "Other")


def create_table():
    commands = [
        # Groups lookup table
        """
        CREATE TABLE IF NOT EXISTS groups (
            id   SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE
        )
        """,

        # Seed the four standard groups (do nothing on conflict)
        """
        INSERT INTO groups (name)
        VALUES ('Family'), ('Work'), ('Friend'), ('Other')
        ON CONFLICT (name) DO NOTHING
        """,

        # Contacts – now with email, birthday, and group FK
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id         SERIAL PRIMARY KEY,
            name       VARCHAR(255) NOT NULL,
            email      VARCHAR(255),
            birthday   DATE,
            group_id   INTEGER REFERENCES groups(id) ON DELETE SET NULL
        )
        """,

        # Phones – 1-to-many, each row carries a type
        """
        CREATE TABLE IF NOT EXISTS phones (
            id         SERIAL PRIMARY KEY,
            contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
            phone      VARCHAR(20) NOT NULL,
            type       VARCHAR(10) NOT NULL DEFAULT 'mobile'
                           CHECK (type IN ('home', 'work', 'mobile'))
        )
        """,
    ]

    with conn.cursor() as cur:
        for cmd in commands:
            cur.execute(cmd)
        conn.commit()


def migrate_table():
    """
    Bring an existing contacts table up to the new schema:
      - add email, birthday, group_id columns if missing
      - migrate old phone column → phones table, then drop it
    Safe to call on a fresh DB (all steps are guarded by IF NOT EXISTS / DO NOTHING).
    """
    migrations = [
        # 1. New columns on contacts (each guarded, so safe to re-run)
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS email    VARCHAR(255)",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS birthday DATE",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL",

        # 2. phones table (idempotent)
        """
        CREATE TABLE IF NOT EXISTS phones (
            id         SERIAL PRIMARY KEY,
            contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
            phone      VARCHAR(20) NOT NULL,
            type       VARCHAR(10) NOT NULL DEFAULT 'mobile'
                           CHECK (type IN ('home', 'work', 'mobile'))
        )
        """,
    ]

    with conn.cursor() as cur:
        for cmd in migrations:
            cur.execute(cmd)

        # 3. If the old 'phone' column still exists, migrate its data then drop it
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'contacts' AND column_name = 'phone'
        """)
        if cur.fetchone():
            print("  Migrating old 'phone' column → phones table …")
            cur.execute("""
                INSERT INTO phones (contact_id, phone, type)
                SELECT id, phone, 'mobile'
                FROM contacts
                WHERE phone IS NOT NULL AND phone <> ''
                  AND id NOT IN (SELECT contact_id FROM phones)
            """)
            cur.execute("ALTER TABLE contacts DROP COLUMN phone")
            print("  Migration done.")

        conn.commit()
    print("Schema is up to date.")


# ============================================================
# Helper: resolve group name → id
# ============================================================

def _group_id(group_name):
    """Return the id for a group name, or None if not provided."""
    if not group_name:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
        row = cur.fetchone()
        if row:
            return row[0]
        raise ValueError(f"Unknown group '{group_name}'. Valid: {VALID_GROUPS}")


# ============================================================
# INSERT
# ============================================================

def insert_contact(name, phones,
                   email=None, birthday=None, group_name=None):
    """
    Insert a contact with one or more phone numbers.

    Args:
        name        – contact name (str)
        phones      – list of (phone, type) tuples, e.g. [("700123", "mobile")]
        email       – optional e-mail address
        birthday    – optional birthday as 'YYYY-MM-DD' string or date object
        group_name  – one of 'Family', 'Work', 'Friend', 'Other' (or None)
    """
    gid = _group_id(group_name)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO contacts (name, email, birthday, group_id) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (name, email, birthday, gid)
        )
        contact_id = cur.fetchone()[0]
        for phone, ptype in phones:
            ptype = ptype.lower() if ptype else "mobile"
            if ptype not in VALID_PHONE_TYPES:
                raise ValueError(f"Invalid phone type '{ptype}'. Use: {VALID_PHONE_TYPES}")
            cur.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                (contact_id, phone, ptype)
            )
        conn.commit()
    print(f"Added: {name} (id={contact_id})")
    return contact_id


def insert_from_console():
    name     = input("Enter name: ")
    email    = input("Enter email (or leave blank): ").strip() or None
    birthday = input("Enter birthday YYYY-MM-DD (or leave blank): ").strip() or None

    print(f"Group options: {VALID_GROUPS}")
    group = input("Enter group (or leave blank): ").strip() or None

    phone_pattern = re.compile(r'^[\d\s\+\-\(\)]+$')
    phones = []
    print(f"Enter phone numbers. Phone types: {VALID_PHONE_TYPES}")
    while True:
        phone = input("  Phone (or leave blank to finish): ").strip()
        if not phone:
            break
        if not phone_pattern.match(phone) or not any(c.isdigit() for c in phone):
            print(f"  Invalid phone '{phone}' — must contain at least one digit. Try again.")
            continue
        ptype = input(f"  Type {VALID_PHONE_TYPES} [mobile]: ").strip() or "mobile"
        if ptype not in VALID_PHONE_TYPES:
            print(f"  Invalid type '{ptype}'. Defaulting to 'mobile'.")
            ptype = "mobile"
        phones.append((phone, ptype))

    if not phones:
        print("At least one phone number is required.")
        return

    insert_contact(name, phones, email=email, birthday=birthday, group_name=group)


def insert_from_csv(csv_file):
    """
    CSV columns (header required):
        name, phone, type, email, birthday, group
    'type', 'email', 'birthday', 'group' may be empty.
    Multiple rows with the same name get their phones merged.
    """
    pending = {}   # name → {email, birthday, group, phones[]}

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nm = row["name"].strip()
            if nm not in pending:
                pending[nm] = {
                    "email":    row.get("email", "").strip() or None,
                    "birthday": row.get("birthday", "").strip() or None,
                    "group":    row.get("group", "").strip() or None,
                    "phones":   [],
                }
            ph = row.get("phone", "").strip()
            pt = row.get("type", "mobile").strip() or "mobile"
            if ph:
                pending[nm]["phones"].append((ph, pt))

    for nm, data in pending.items():
        insert_contact(nm, data["phones"],
                       email=data["email"],
                       birthday=data["birthday"],
                       group_name=data["group"])

    print(f"Imported contacts from {csv_file}")


# ============================================================
# SELECT (rich view joining all tables)
# ============================================================

_FULL_SELECT = """
    SELECT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name  AS group_name,
        p.phone,
        p.type  AS phone_type
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
"""


def _rows_to_contacts(rows):
    """
    Collapse flat join rows into a list of contact dicts.
    Each dict: {id, name, email, birthday, group, phones: [(phone, type), …]}
    """
    contacts = {}
    for row in rows:
        cid, name, email, birthday, group, phone, ptype = row
        if cid not in contacts:
            contacts[cid] = {
                "id":       cid,
                "name":     name,
                "email":    email,
                "birthday": birthday,
                "group":    group,
                "phones":   [],
            }
        if phone:
            contacts[cid]["phones"].append((phone, ptype))
    return list(contacts.values())


def get_all_contacts():
    with conn.cursor() as cur:
        cur.execute(_FULL_SELECT + " ORDER BY c.name, p.type")
        return _rows_to_contacts(cur.fetchall())


def search_contacts(pattern):
    query = _FULL_SELECT + """
        WHERE c.name ILIKE %s OR p.phone ILIKE %s
        ORDER BY c.name, p.type
    """
    like = f"%{pattern}%"
    with conn.cursor() as cur:
        cur.execute(query, (like, like))
        return _rows_to_contacts(cur.fetchall())


def search_by_pattern(pattern):
    """Search by name fragment, phone fragment, email, or group name."""
    query = _FULL_SELECT + """
        WHERE c.name  ILIKE %s
           OR p.phone ILIKE %s
           OR c.email ILIKE %s
           OR g.name  ILIKE %s
        ORDER BY c.name, p.type
    """
    like = f"%{pattern}%"
    with conn.cursor() as cur:
        cur.execute(query, (like, like, like, like))
        return _rows_to_contacts(cur.fetchall())


# ============================================================
# UPDATE
# ============================================================

def update_phone(contact_id, old_phone, new_phone):
    """Update a specific phone number for a contact."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE phones SET phone = %s "
            "WHERE contact_id = %s AND phone = %s",
            (new_phone, contact_id, old_phone)
        )
        conn.commit()
        print(f"Updated {cur.rowcount} phone row(s)")


def update_phone_type(contact_id, phone, new_type):
    """Change the type (home/work/mobile) of a phone number."""
    if new_type not in VALID_PHONE_TYPES:
        raise ValueError(f"Invalid type '{new_type}'. Use: {VALID_PHONE_TYPES}")
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE phones SET type = %s "
            "WHERE contact_id = %s AND phone = %s",
            (new_type, contact_id, phone)
        )
        conn.commit()
        print(f"Updated {cur.rowcount} phone row(s)")


def update_contact_info(contact_id, name=None, email=None,
                        birthday=None, group_name=None):
    """
    Partially update a contact's own fields.
    Pass only the fields you want to change; others remain untouched.
    """
    fields, values = [], []
    if name is not None:
        fields.append("name = %s");     values.append(name)
    if email is not None:
        fields.append("email = %s");    values.append(email)
    if birthday is not None:
        fields.append("birthday = %s"); values.append(birthday)
    if group_name is not None:
        gid = _group_id(group_name)
        fields.append("group_id = %s"); values.append(gid)

    if not fields:
        print("Nothing to update.")
        return

    values.append(contact_id)
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE contacts SET {', '.join(fields)} WHERE id = %s",
            values
        )
        conn.commit()
        print(f"Updated {cur.rowcount} contact row(s)")


def add_phone(contact_id, phone, ptype="mobile"):
    """Add an extra phone number to an existing contact."""
    if ptype not in VALID_PHONE_TYPES:
        raise ValueError(f"Invalid type '{ptype}'. Use: {VALID_PHONE_TYPES}")
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
            (contact_id, phone, ptype)
        )
        conn.commit()
    print(f"Phone {phone} ({ptype}) added to contact {contact_id}")


# ============================================================
# DELETE
# ============================================================

def delete_by_name(name):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM contacts WHERE name = %s", (name,))
        conn.commit()
        print(f"Deleted {cur.rowcount} row(s)")


def delete_by_phone(phone):
    """Delete the phone row; if the contact has no more phones, keep contact."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM phones WHERE phone = %s", (phone,))
        conn.commit()
        print(f"Deleted {cur.rowcount} phone row(s)")


def delete_by_name_or_phone(identifier):
    with conn.cursor() as cur:
        # Delete matching phone rows first
        cur.execute("DELETE FROM phones WHERE phone = %s", (identifier,))
        phones_deleted = cur.rowcount
        # Delete contacts whose name matches
        cur.execute("DELETE FROM contacts WHERE name = %s", (identifier,))
        contacts_deleted = cur.rowcount
        conn.commit()
        print(f"Deleted {contacts_deleted} contact(s) and "
              f"{phones_deleted} phone row(s) matching '{identifier}'")


def delete_contact_by_id(contact_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
        conn.commit()
        print(f"Deleted {cur.rowcount} contact(s) with id={contact_id}")


# ============================================================
# UPSERT
# ============================================================

def upsert_contact(name, phones, email=None, birthday=None, group_name=None):
    """
    Insert a new contact, or update their info if the name already exists.
    For existing contacts, new phone numbers are added (no duplicates).
    """
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
        row = cur.fetchone()

    if row:
        contact_id = row[0]
        update_contact_info(contact_id, name=name, email=email,
                            birthday=birthday, group_name=group_name)
        # Add new phones only
        with conn.cursor() as cur:
            cur.execute("SELECT phone FROM phones WHERE contact_id = %s", (contact_id,))
            existing_phones = {r[0] for r in cur.fetchall()}
        for phone, ptype in phones:
            if phone not in existing_phones:
                add_phone(contact_id, phone, ptype)
        print(f"Upserted (updated) contact '{name}' id={contact_id}")
    else:
        contact_id = insert_contact(name, phones, email=email,
                                    birthday=birthday, group_name=group_name)
        print(f"Upserted (inserted) contact '{name}' id={contact_id}")


# ============================================================
# BULK INSERT
# ============================================================

def insert_many_contacts(contacts_list):
    """
    Bulk-insert contacts.

    Args:
        contacts_list – list of dicts with keys:
            name      (required)
            phones    list of (phone, type) tuples (required, at least one)
            email     optional
            birthday  optional 'YYYY-MM-DD'
            group     optional group name

    Returns:
        list of dicts that failed validation
    """
    phone_pattern = re.compile(r'^[\d\s\+\-\(\)]+$')
    invalid_entries = []

    for entry in contacts_list:
        name    = (entry.get("name") or "").strip()
        phones  = entry.get("phones") or []
        email   = entry.get("email") or None
        birthday= entry.get("birthday") or None
        group   = entry.get("group") or None

        if not name:
            print(f"  [INVALID] Empty name — skipped: {entry}")
            invalid_entries.append(entry)
            continue

        valid_phones = []
        bad = False
        for phone, ptype in phones:
            if not phone_pattern.match(phone.strip()):
                print(f"  [INVALID] Bad phone '{phone}' for '{name}' — skipped")
                bad = True
                break
            ptype = (ptype or "mobile").strip().lower()
            if ptype not in VALID_PHONE_TYPES:
                print(f"  [INVALID] Bad phone type '{ptype}' for '{name}' — skipped")
                bad = True
                break
            valid_phones.append((phone.strip(), ptype))

        if bad or not valid_phones:
            invalid_entries.append(entry)
            continue

        try:
            upsert_contact(name, valid_phones, email=email,
                           birthday=birthday, group_name=group)
        except Exception as exc:
            print(f"  [ERROR] {name}: {exc}")
            invalid_entries.append(entry)

    valid_count = len(contacts_list) - len(invalid_entries)
    print(f"\nInserted/updated {valid_count} contact(s). "
          f"{len(invalid_entries)} invalid entry/entries skipped.")
    return invalid_entries


# ============================================================
# PAGINATION
# ============================================================

def get_contacts_paginated(page=1, page_size=10):
    offset = (page - 1) * page_size
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM contacts")
        total_count = cur.fetchone()[0]

        cur.execute(
            _FULL_SELECT + " ORDER BY c.name, p.type LIMIT %s OFFSET %s",
            (page_size * 5, offset * 5)   # over-fetch to cover multi-phone rows
        )
        all_rows = _rows_to_contacts(cur.fetchall())

    # Re-slice at the contact level
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM contacts ORDER BY name LIMIT %s OFFSET %s",
            (page_size, offset)
        )
        page_ids = {r[0] for r in cur.fetchall()}

    page_contacts = [c for c in all_rows if c["id"] in page_ids]
    return page_contacts, total_count


# ============================================================
# Display helper
# ============================================================

def print_contacts(contacts):
    if not contacts:
        print("  (no contacts)")
        return
    for c in contacts:
        phones_str = ", ".join(f"{ph} ({pt})" for ph, pt in c["phones"]) or "—"
        bday  = c["birthday"] or "—"
        email = c["email"]    or "—"
        group = c["group"]    or "—"
        print(f"  [{c['id']}] {c['name']}")
        print(f"       Phones:   {phones_str}")
        print(f"       Email:    {email}  |  Birthday: {bday}  |  Group: {group}")


# ============================================================
# Main menu
# ============================================================

def main():
    create_table()
    migrate_table()

    while True:
        print("\n--- PhoneBook ---")
        print("1.  Show all contacts")
        print("2.  Add contact (console)")
        print("3.  Import from CSV")
        print("4.  Search")
        print("5.  Update contact info (name / email / birthday / group)")
        print("6.  Update phone number")
        print("7.  Change phone type")
        print("8.  Add phone to existing contact")
        print("9.  Delete by name")
        print("10. Delete phone number")
        print("11. Delete contact by id")
        print("--- New features ---")
        print("12. Search by pattern (name / phone / email / group)")
        print("13. Upsert contact (insert or update)")
        print("14. Bulk insert with validation")
        print("15. Browse contacts with pagination")
        print("16. Delete by name OR phone")
        print("0.  Exit")

        choice = input("\nChoice: ").strip()

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
            cid   = int(input("Contact ID: "))
            name  = input("New name (blank = keep): ").strip() or None
            email = input("New email (blank = keep): ").strip() or None
            bday  = input("New birthday YYYY-MM-DD (blank = keep): ").strip() or None
            print(f"Group options: {VALID_GROUPS}")
            grp   = input("New group (blank = keep): ").strip() or None
            update_contact_info(cid, name=name, email=email,
                                birthday=bday, group_name=grp)

        elif choice == "6":
            cid       = int(input("Contact ID: "))
            old_phone = input("Old phone: ").strip()
            new_phone = input("New phone: ").strip()
            update_phone(cid, old_phone, new_phone)

        elif choice == "7":
            cid   = int(input("Contact ID: "))
            phone = input("Phone number: ").strip()
            print(f"Type options: {VALID_PHONE_TYPES}")
            ptype = input("New type: ").strip()
            update_phone_type(cid, phone, ptype)

        elif choice == "8":
            cid   = int(input("Contact ID: "))
            phone = input("Phone: ").strip()
            print(f"Type options: {VALID_PHONE_TYPES}")
            ptype = input("Type [mobile]: ").strip() or "mobile"
            add_phone(cid, phone, ptype)

        elif choice == "9":
            name = input("Name: ")
            delete_by_name(name)

        elif choice == "10":
            phone = input("Phone number to delete: ")
            delete_by_phone(phone)

        elif choice == "11":
            cid = int(input("Contact ID: "))
            delete_contact_by_id(cid)

        elif choice == "12":
            pattern = input("Enter pattern: ")
            print_contacts(search_by_pattern(pattern))

        elif choice == "13":
            name  = input("Name: ")
            email = input("Email (blank = none): ").strip() or None
            bday  = input("Birthday YYYY-MM-DD (blank = none): ").strip() or None
            print(f"Group options: {VALID_GROUPS}")
            grp   = input("Group (blank = none): ").strip() or None
            phones = []
            print(f"Enter phone numbers. Type options: {VALID_PHONE_TYPES}")
            while True:
                ph = input("  Phone (blank to finish): ").strip()
                if not ph:
                    break
                pt = input(f"  Type [mobile]: ").strip() or "mobile"
                phones.append((ph, pt))
            upsert_contact(name, phones, email=email,
                           birthday=bday, group_name=grp)

        elif choice == "14":
            print("Enter contacts in format: Name,Phone,Type,Email,Birthday,Group")
            print("Example: Alice,+7700123,mobile,alice@mail.com,1990-05-20,Work")
            print("Empty line to finish.")
            entries = []
            while True:
                line = input("  > ").strip()
                if not line:
                    break
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 2:
                    print("  Need at least Name,Phone")
                    continue
                name  = parts[0]
                phone = parts[1]
                ptype = parts[2] if len(parts) > 2 and parts[2] else "mobile"
                email = parts[3] if len(parts) > 3 and parts[3] else None
                bday  = parts[4] if len(parts) > 4 and parts[4] else None
                grp   = parts[5] if len(parts) > 5 and parts[5] else None
                entries.append({"name": name, "phones": [(phone, ptype)],
                                 "email": email, "birthday": bday, "group": grp})
            invalid = insert_many_contacts(entries)
            if invalid:
                print("\nInvalid entries:")
                for e in invalid:
                    print(f"  {e}")

        elif choice == "15":
            page_size = int(input("Records per page [10]: ").strip() or "10")
            page = 1
            while True:
                rows, total = get_contacts_paginated(page, page_size)
                total_pages = max(1, -(-total // page_size))
                print(f"\n  Page {page}/{total_pages}  (total: {total} contacts)")
                print_contacts(rows)
                nav = input("  [n]ext / [p]rev / [q]uit: ").strip().lower()
                if nav == "n" and page < total_pages:
                    page += 1
                elif nav == "p" and page > 1:
                    page -= 1
                elif nav == "q":
                    break

        elif choice == "16":
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