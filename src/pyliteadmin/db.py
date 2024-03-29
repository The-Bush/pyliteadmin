import sqlite3

def get_columns(table:str) -> list:
    """ Returns a list of column names and types for a given table """
    # Import the path to the database
    from pyliteadmin.app import db_path
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    columns = [description[0] for description in cursor.description]
    conn.close()
    return columns

def get_table(table:str) -> tuple[list[tuple], list[str]]:
    """ Returns a list of rows as tuples and a list of column names for a given table """
    # Import the path to the database
    from pyliteadmin.app import db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")

    # Get all items in this table
    rows = cursor.fetchall()

    # Get the column names
    columns = get_columns(table)

    conn.close
    return rows, columns

def get_table_page(table:str, offset:int, limit:int) -> tuple[list[tuple], list[str]]:
    """ Returns a list of rows as tuples and a list of column names for a given table """
    # Import the path to the database
    from pyliteadmin.app import db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} LIMIT {limit} OFFSET {offset}")

    # Get all items in this table
    rows = cursor.fetchall()

    # Get the column names
    columns = get_columns(table)

    conn.close
    return rows, columns

def search_table(table:str, search_column:str, search_value:str) -> list[tuple]:
    """ Returns a list of rows as tuples for a given table and search value and search column """
    # Import the path to the database
    from pyliteadmin.app import db_path
    
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
    # Import the path to the database
    from pyliteadmin.app import db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sorted(table_names)

def delete_row(table:str, row:tuple, columns:list) -> None:
    """ Delete the currently selected row"""
    # Import the path to the database
    from pyliteadmin.app import db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = ""

    # Generate the query
    for i, column in enumerate(row):
        if i > 0:
            query += " AND "
        if column == None:
            query += f"{columns[i]} IS NULL"
        else:
            query += f"{columns[i]} = '{column}'"

    print(f"DELETE FROM {table} WHERE {query}")

    try:
        cursor.execute(f"DELETE FROM {table} WHERE {query}")

    except Exception as error:
        conn.close()
        error_message = f"Error: {error}"
        raise Exception(error_message)
    
    conn.commit()
    conn.close()

def update_cell(table:str, row: tuple, column:str, columns: list, new_value:str):
    """ Update the selected sell with its new value """
    # Import the path to the database
    from pyliteadmin.app import db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = ""
    
    # Generate the query
    for i, value in enumerate(row):
        if i > 0:
            query += " AND "
        if value == None:
            query += f"{columns[i]} IS NULL"
        else:
            query += f"{columns[i]} = '{value}'"
            
    print(f"UPDATE {table} SET {column} = '{new_value}' WHERE {query}")

    try:
        cursor.execute(f"UPDATE {table} SET {column} = '{new_value}' WHERE {query}")
    except Exception as error:
        conn.close()
        error_message = f"Error: {error}"
        raise Exception(error_message)
    
    conn.commit()
    conn.close()

def add_row(table:str, row:tuple) -> None:
    """ Add a new row to the database """
    # Import the path to the database
    from pyliteadmin.app import db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = ""

    # Generate the query
    for i, value in enumerate(row):
        if i > 0:
            query += ", "
        if value == None:
            query += "NULL"
        else:
            query += f"'{value}'"

    print(f"INSERT INTO {table} VALUES ({query})")

    try:
        cursor.execute(f"INSERT INTO {table} VALUES ({query})")
    except Exception as error:
        conn.close()
        error_message = f"Error: {error}"
        raise Exception(error_message)
    
    conn.commit()
    conn.close()

def get_row_count(table:str) -> int:
    """ Returns the number of rows in a table """
    # Import the path to the database
    from pyliteadmin.app import db_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row_count = cursor.fetchone()[0]
    conn.close()
    return row_count