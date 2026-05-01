import psycopg2

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
