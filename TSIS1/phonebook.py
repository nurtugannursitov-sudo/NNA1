import psycopg2
import csv
import json
from datetime import datetime

# ================= CONFIG =================
DB_CONFIG = {
    "host": "localhost",
    "database": "phonebook",
    "user": "postgres",
    "password": "postgres"
}

conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = False

# ================= DB SETUP =================

def create_tables():
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255),
            birthday DATE,
            group_id INTEGER REFERENCES groups(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS phones (
            id SERIAL PRIMARY KEY,
            contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
            phone VARCHAR(20),
            type VARCHAR(10) CHECK (type IN ('home','work','mobile'))
        );
        """)

        # ── VIEW: объединяет все три таблицы ──────────────────────────────────
        # В pgAdmin / psql: SELECT * FROM phonebook_view;
        cur.execute("""
        CREATE OR REPLACE VIEW phonebook_view AS
        SELECT
            c.id,
            c.name,
            c.email,
            c.birthday,
            COALESCE(g.name, 'Other')                                      AS grp,
            COALESCE(
                string_agg(p.phone || ' (' || p.type || ')', ', '
                           ORDER BY p.type),
                NULL
            )                                                               AS phones,
            c.created_at
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id       = p.contact_id
        GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at;
        """)
        conn.commit()

# ================= HELPERS =================

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

# ================= CONTACT + PHONE (объединённое добавление) =================

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

    # --- сразу добавляем телефоны ---
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

# ================= ДОБАВИТЬ ТЕЛЕФОН К СУЩЕСТВУЮЩЕМУ КОНТАКТУ =================

def add_phone():
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

# ================= УДАЛЕНИЕ =================

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

        # показываем что будет удалено
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

        # телефоны удалятся каскадно (ON DELETE CASCADE)
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

# ================= SEARCH =================

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

# ================= ПОЛНЫЙ СПИСОК (contacts + phones + groups) =================

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

    # заголовок таблицы
    header = f"{'Name':<25} {'Group':<12} {'Email':<25} {'Birthday':<12} {'Added':<12} Phones"
    print("\n" + header)
    print("-" * len(header) + "-" * 20)

    for name, grp, email, birthday, added, phones in rows:
        print(
            f"{name:<25} {grp:<12} {(email or '—'):<25} "
            f"{str(birthday or '—'):<12} {str(added):<12} {phones}"
        )

# ================= FILTER =================

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

# ================= PAGINATION =================

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

# ================= JSON =================

def export_json():
    """
    Экспортирует контакты в contacts.json.
    Формат: список объектов, у каждого телефоны — вложенный список.
    [
      {
        "name": "Иван",
        "email": "ivan@mail.ru",
        "birthday": "1990-05-10",
        "group": "Friends",
        "phones": [
          {"phone": "+7999...", "type": "mobile"},
          {"phone": "+7888...", "type": "work"}
        ]
      },
      ...
    ]
    """
    with conn.cursor() as cur:
        # Сначала берём все контакты
        cur.execute("""
            SELECT c.id, c.name, c.email, c.birthday, COALESCE(g.name, 'Other') AS grp
            FROM contacts c
            LEFT JOIN groups g ON c.group_id = g.id
            ORDER BY c.name
        """)
        contacts = cur.fetchall()

        data = []
        for cid, name, email, birthday, grp in contacts:
            # Для каждого контакта достаём его телефоны
            cur.execute(
                "SELECT phone, type FROM phones WHERE contact_id=%s ORDER BY type",
                (cid,)
            )
            phones = [{"phone": ph, "type": pt} for ph, pt in cur.fetchall()]

            data.append({
                "name":     name,
                "email":    email,
                "birthday": str(birthday) if birthday else None,
                "group":    grp,
                "phones":   phones
            })

    with open("contacts.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(data)} contacts to contacts.json")


def import_json():
    """
    Импортирует контакты из contacts.json.
    Ожидает тот же формат, что генерирует export_json():
    каждый контакт — объект с полем "phones" (список).
    При конфликте имени спрашивает skip/overwrite один раз на контакт.
    """
    with open("contacts.json", encoding="utf-8") as f:
        data = json.load(f)

    imported = skipped = 0

    for entry in data:
        name     = entry.get("name", "").strip()
        email    = entry.get("email") or None
        birthday = entry.get("birthday") or None
        group    = entry.get("group") or "Other"
        phones   = entry.get("phones", [])   # список {"phone": ..., "type": ...}

        if not name:
            print("Skipping entry with no name.")
            continue

        with conn.cursor() as cur:
            cur.execute("SELECT id FROM contacts WHERE name=%s", (name,))
            existing = cur.fetchone()

            if existing:
                choice = input(f"'{name}' already exists. (skip/overwrite): ").strip().lower()
                if choice == "skip":
                    skipped += 1
                    continue
                # overwrite: удаляем старый контакт (телефоны удалятся каскадно)
                cur.execute("DELETE FROM contacts WHERE name=%s", (name,))

            gid = get_or_create_group(group)

            cur.execute(
                """INSERT INTO contacts(name, email, birthday, group_id)
                   VALUES(%s, %s, %s, %s) RETURNING id""",
                (name, email, safe_date(birthday) if birthday else None, gid)
            )
            cid = cur.fetchone()[0]

            for p in phones:
                ph    = p.get("phone", "").strip()
                ptype = p.get("type", "").strip().lower()
                if ph and ptype in ("home", "work", "mobile"):
                    cur.execute(
                        "INSERT INTO phones(contact_id, phone, type) VALUES(%s,%s,%s)",
                        (cid, ph, ptype)
                    )
                else:
                    print(f"  Skipped invalid phone entry for '{name}': {p}")

            conn.commit()
            imported += 1

    print(f"Import done: {imported} imported, {skipped} skipped.")

# ================= CSV =================

def import_csv():
    file = input("CSV file: ").strip()
    try:
        with open(file, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            # Показываем найденные колонки для диагностики
            rows = list(reader)
            if not rows:
                print("CSV file is empty.")
                return
            
            print(f"Columns found: {list(rows[0].keys())}")
            
            imported = skipped = 0
            for r in rows:
                # Гибко читаем колонки — берём что есть
                name     = (r.get('name') or r.get('Name') or '').strip()
                email    = (r.get('email') or r.get('Email') or '').strip() or None
                birthday = (r.get('birthday') or r.get('Birthday') or '').strip() or None
                group    = (r.get('group') or r.get('Group') or 'Other').strip() or 'Other'
                phone    = (r.get('phone') or r.get('Phone') or '').strip()
                ptype    = (r.get('type') or r.get('Type') or 'mobile').strip().lower()

                if not name:
                    print(f"  Skipping row with no name: {dict(r)}")
                    skipped += 1
                    continue

                if ptype not in ('home', 'work', 'mobile'):
                    print(f"  Invalid phone type '{ptype}' for '{name}', defaulting to 'mobile'.")
                    ptype = 'mobile'

                gid = get_or_create_group(group)

                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO contacts(name, email, birthday, group_id)
                        VALUES(%s, %s, %s, %s)
                        ON CONFLICT (name) DO UPDATE
                        SET email=EXCLUDED.email,
                            birthday=EXCLUDED.birthday,
                            group_id=EXCLUDED.group_id
                        RETURNING id
                    """, (name, email, safe_date(birthday) if birthday else None, gid))
                    cid = cur.fetchone()[0]

                    if phone:
                        cur.execute(
                            "INSERT INTO phones(contact_id, phone, type) VALUES(%s,%s,%s)",
                            (cid, phone, ptype)
                        )
                    conn.commit()
                    imported += 1

            print(f"Import done: {imported} imported, {skipped} skipped.")

    except FileNotFoundError:
        print(f"File not found: {file}")
    except Exception as e:
        conn.rollback()
        print(f"Error during import: {e}")

# ================= MENU =================

def main():
    create_tables()

    while True:
        print("""
1  Add contact (+ phones at once)
2  Add phone to existing contact
3  Delete contact
4  Delete phone number
5  Search
6  Filter by group
7  Browse (pagination)
8  List ALL contacts with phones & groups
9  Export JSON
10 Import JSON
11 Import CSV
0  Exit
""")
        c = input("Choice: ")

        if   c == "1":  add_contact()
        elif c == "2":  add_phone()
        elif c == "3":  delete_contact()
        elif c == "4":  delete_phone()
        elif c == "5":  print(search_contacts(input("Search: ")))
        elif c == "6":  print(filter_by_group())
        elif c == "7":  browse_contacts()
        elif c == "8":  list_all()
        elif c == "9":  export_json()
        elif c == "10": import_json()
        elif c == "11": import_csv()
        elif c == "0":  break

    conn.close()

if __name__ == "__main__":
    main()