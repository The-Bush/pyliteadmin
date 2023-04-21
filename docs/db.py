import sqlite3

# Import the path to the database
from pyliteadmin import db_path

def get_table(table:str) -> tuple[list[tuple], list[str]]:
    """ Returns a list of rows as tuples and a list of column names for a given table """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")

    # Get all items in this table
    rows = cursor.fetchall()

    # Get the column names
    columns = [description[0] for description in cursor.description]

    conn.close
    return rows, columns

def search_table(table:str, search_column:str, search_value:str) -> list[tuple]:
    """ TODO """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE {search_column} = '{search_value}'", (table, search_column, search_value))

    # Get all items in this search result
    rows = cursor.fetchall()

    # Get the column names
    columns = [description[0] for description in cursor.description]

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