from db import conn, create_tables
from contacts import (
    add_contact, add_phone,
    delete_contact, delete_phone,
    search_contacts, list_all,
    filter_by_group, browse_contacts,
)
from io_utils import export_json, import_json, import_csv


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
