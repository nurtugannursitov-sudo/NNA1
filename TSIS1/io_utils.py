import csv
import json
from db import conn
from contacts import get_or_create_group, safe_date


# ================= JSON =================

def export_json():
    """Экспортирует контакты в contacts.json."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.id, c.name, c.email, c.birthday, COALESCE(g.name, 'Other') AS grp
            FROM contacts c
            LEFT JOIN groups g ON c.group_id = g.id
            ORDER BY c.name
        """)
        contacts = cur.fetchall()

        data = []
        for cid, name, email, birthday, grp in contacts:
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
    """Импортирует контакты из contacts.json."""
    with open("contacts.json", encoding="utf-8") as f:
        data = json.load(f)

    imported = skipped = 0

    for entry in data:
        name     = entry.get("name", "").strip()
        email    = entry.get("email") or None
        birthday = entry.get("birthday") or None
        group    = entry.get("group") or "Other"
        phones   = entry.get("phones", [])

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
            rows = list(reader)

            if not rows:
                print("CSV file is empty.")
                return

            print(f"Columns found: {list(rows[0].keys())}")

            imported = skipped = 0
            for r in rows:
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
