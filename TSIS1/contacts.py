from datetime import datetime
from db import conn


#HELPERS

def get_or_create_group(name: str):
    name = (name or "Other").strip()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM groups WHERE name=%s", (name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO groups(name) VALUES(%s) RETURNING id", (name,))
        gid = cur.fetchone()[0]
        conn.commit()
        return gid


def safe_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        print("Invalid date format. Use YYYY-MM-DD. Skipped.")
        return None


#ADD
def add_contact():
    """Добавляет контакт и сразу предлагает добавить телефоны."""
    name = input("Name: ").strip()
    if not name:
        print("Name required")
        return

    email    = input("Email: ").strip() or None
    birthday = safe_date(input("Birthday (YYYY-MM-DD): ").strip())
    group    = input("Group: ").strip() or "Other"

    gid = get_or_create_group(group)

    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO contacts(name,email,birthday,group_id)
        VALUES(%s,%s,%s,%s)
        ON CONFLICT (name) DO UPDATE
        SET email=EXCLUDED.email,
            birthday=EXCLUDED.birthday,
            group_id=EXCLUDED.group_id
        RETURNING id
        """, (name, email, birthday, gid))
        contact_id = cur.fetchone()[0]
        conn.commit()

    print(f"Contact '{name}' saved.")

    while True:
        add_more = input("Add phone number? (y/n): ").strip().lower()
        if add_more != "y":
            break

        phone = input("  Phone: ").strip()
        ptype = input("  Type (home/work/mobile): ").strip().lower()

        if ptype not in ("home", "work", "mobile"):
            print("  Invalid type, skipped.")
            continue

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO phones(contact_id,phone,type) VALUES(%s,%s,%s)",
                (contact_id, phone, ptype)
            )
            conn.commit()
        print(f"  Phone {phone} ({ptype}) added.")


def add_phone():
    """Добавляет телефон к существующему контакту."""
    name  = input("Contact name: ").strip()
    phone = input("Phone: ").strip()
    ptype = input("Type (home/work/mobile): ").strip().lower()

    if ptype not in ("home", "work", "mobile"):
        print("Invalid type")
        return

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM contacts WHERE name=%s", (name,))
        row = cur.fetchone()
        if not row:
            print("Contact not found")
            return

        cur.execute("INSERT INTO phones(contact_id,phone,type) VALUES(%s,%s,%s)",
                    (row[0], phone, ptype))
        conn.commit()
    print("Phone added.")


# DELETE 

def delete_contact():
    name = input("Contact name to delete: ").strip()
    if not name:
        print("Name required")
        return

    with conn.cursor() as cur:
        cur.execute("SELECT id, email FROM contacts WHERE name=%s", (name,))
        row = cur.fetchone()
        if not row:
            print(f"Contact '{name}' not found.")
            return

        contact_id, email = row

        cur.execute("SELECT phone, type FROM phones WHERE contact_id=%s", (contact_id,))
        phones = cur.fetchall()

        print(f"\n  Name   : {name}")
        print(f"  Email  : {email or '—'}")
        if phones:
            for ph, pt in phones:
                print(f"  Phone  : {ph} ({pt})")
        else:
            print("  Phones : —")

        confirm = input("\nDelete this contact? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            return

        cur.execute("DELETE FROM contacts WHERE id=%s", (contact_id,))
        conn.commit()

    print(f"Contact '{name}' deleted.")


def delete_phone():
    """Удаляет один конкретный номер, не трогая контакт."""
    name = input("Contact name: ").strip()

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM contacts WHERE name=%s", (name,))
        row = cur.fetchone()
        if not row:
            print("Contact not found.")
            return

        contact_id = row[0]
        cur.execute("SELECT id, phone, type FROM phones WHERE contact_id=%s", (contact_id,))
        phones = cur.fetchall()

    if not phones:
        print("No phones for this contact.")
        return

    print("\nPhones:")
    for i, (pid, ph, pt) in enumerate(phones, 1):
        print(f"  {i}. {ph} ({pt})")

    choice = input("Number to delete (or 0 to cancel): ").strip()
    if not choice.isdigit() or int(choice) == 0:
        print("Cancelled.")
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(phones):
        print("Invalid choice.")
        return

    pid, ph, pt = phones[idx]
    with conn.cursor() as cur:
        cur.execute("DELETE FROM phones WHERE id=%s", (pid,))
        conn.commit()
    print(f"Phone {ph} ({pt}) deleted.")


#SEARCH / LIST 

def search_contacts(query):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT c.name, c.email, c.birthday, g.name AS grp, p.phone, p.type
        FROM contacts c
        LEFT JOIN groups  g ON c.group_id = g.id
        LEFT JOIN phones  p ON c.id       = p.contact_id
        WHERE c.name  ILIKE %s
           OR c.email ILIKE %s
           OR p.phone ILIKE %s
        ORDER BY c.name
        """, (f"%{query}%",) * 3)
        return cur.fetchall()


def list_all():
    """Выводит все контакты вместе с телефонами и группами в читаемом виде."""
    with conn.cursor() as cur:
        cur.execute("""
        SELECT
            c.name,
            COALESCE(g.name, 'Other')  AS grp,
            c.email,
            c.birthday,
            c.created_at::date,
            COALESCE(
                string_agg(p.phone || ' (' || p.type || ')', ', ' ORDER BY p.type),
                '—'
            ) AS phones
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id       = p.contact_id
        GROUP BY c.id, c.name, g.name, c.email, c.birthday, c.created_at
        ORDER BY c.name
        """)
        rows = cur.fetchall()

    if not rows:
        print("No contacts found.")
        return

    header = f"{'Name':<25} {'Group':<12} {'Email':<25} {'Birthday':<12} {'Added':<12} Phones"
    print("\n" + header)
    print("-" * len(header) + "-" * 20)

    for name, grp, email, birthday, added, phones in rows:
        print(
            f"{name:<25} {grp:<12} {(email or '—'):<25} "
            f"{str(birthday or '—'):<12} {str(added):<12} {phones}"
        )


def filter_by_group():
    g = input("Group: ").strip()
    with conn.cursor() as cur:
        cur.execute("""
        SELECT c.name, c.email
        FROM contacts c
        JOIN groups g ON c.group_id = g.id
        WHERE g.name = %s
        """, (g,))
        return cur.fetchall()


def browse_contacts():
    allowed_sort = {"name": "name", "birthday": "birthday", "created_at": "created_at"}
    user_input = input("Sort by (name/birthday/created_at): ").lower()
    sort = allowed_sort.get(user_input, "name")

    page = 1
    size = 5

    while True:
        offset = (page - 1) * size
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT name, email FROM contacts ORDER BY {sort} LIMIT %s OFFSET %s",
                (size, offset)
            )
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) FROM contacts")
            total = cur.fetchone()[0]

        total_pages = max(1, (total + size - 1) // size)

        print(f"\nPage {page}/{total_pages}")
        for r in rows:
            print(r)

        cmd = input("n/p/q: ").lower()
        if cmd == "n" and page < total_pages:
            page += 1
        elif cmd == "p" and page > 1:
            page -= 1
        elif cmd == "q":
            break
