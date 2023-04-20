import sqlite3

database_path="chinook.db"

def get_table(table:str) -> tuple[list[tuple], list[str]]:
    conn = sqlite3.connect("chinook.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} LIMIT 10")

    # Get all items in this db
    rows = cursor.fetchall()

    # Get the column names
    columns = [description[0] for description in cursor.description]

    return rows, columns


def get_table_names(database_path: str) -> list:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return table_names