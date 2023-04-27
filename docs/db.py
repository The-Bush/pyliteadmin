import sqlite3

# Import the path to the database
from pyliteadmin import db_path

def get_columns(table:str) -> list:
    """ Returns a list of column names and types for a given table """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    columns = [description[0] for description in cursor.description]
    conn.close()
    return columns

def get_table(table:str) -> tuple[list[tuple], list[str]]:
    """ Returns a list of rows as tuples and a list of column names for a given table """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")

    # Get all items in this table
    rows = cursor.fetchall()

    # Get the column names
    columns = get_columns(table)

    conn.close
    return rows, columns

def search_table(table:str, search_column:str, search_value:str) -> list[tuple]:
    """ TODO """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE {search_column} LIKE '%{search_value}%'")

    # Get all items in this search result
    rows = cursor.fetchall()

    # Get the column names
    columns = get_columns(table)

    conn.close
    return rows, columns

def get_table_names() -> list:
    """ Returns a list of table names from the current database """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sorted(table_names)

def delete_row(table:str, row:tuple, columns:list) -> None:
    """ TODO """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = ""

    for i, column in enumerate(row):
        if i > 0:
            query += " AND "
        query += f"{columns[i]} = '{column}'"

    print(f"DELETE FROM {table} WHERE {query}")
    cursor.execute(f"DELETE FROM {table} WHERE {query}")
    conn.commit()
    conn.close()