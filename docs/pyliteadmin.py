import os
from itertools import cycle
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Button,
    Header,
    Footer,
    DataTable,
    Static,
    ListView,
    ListItem,
    Label,
)
import sqlite3
import db

# Set the table cursor to a cycle of three different cursor types
cursors = cycle(["column", "row", "cell"])

# Take command line argument for the path to the database
# If no command line argument is given, return error and exit
if len(os.sys.argv) > 1:
    db_path = os.sys.argv[1]
else:

    print("No database path given.\nUSAGE: pyliteadmin.py <path to database>")
    exit()


class TableSelector(Widget):
    """A widget that allows the selection of a table from the selected database"""

    def compose(self) -> ComposeResult:
        yield Label("Table Selector", id="table-selector-label")
        yield ListView(id="options")

    # On Mount, list all tables files in current working db
    def on_mount(self) -> None:
        table_names = db.get_table_names()
        for table in table_names:
            new_listitem = ListItem(Label(table, id="label"))
            self.query_one("#options").append(new_listitem)


class TableViewer(Widget):
    """A widget that displays the contents of a selected table"""

    def __init__(self, table: str) -> None:
        super().__init__()
        self.table = table
        self.rows, self.columns = db.get_table(f"{table}")

    def compose(self) -> ComposeResult:
        yield DataTable(id="table")

    def on_mount(self) -> None:
        table = self.table
        rows, columns = db.get_table(f"{table}")
        data_table = self.query_one(DataTable)
        data_table.add_columns(*columns)
        data_table.add_rows(rows)


class TableSearch(Widget):
    """A widget that allows the searching within a table a table"""

    def __init__(self, table: str, search_column: str, search_term: str) -> None:
        super().__init__()
        self.table = table
        self.search_column = search_column
        self.search_term = search_term
        self.rows, self.columns = db.get_table(f"{table}")


class PyLiteAdmin(App):
    """A terminal app to manage sqlite databases in a graphical interface"""

    CSS_PATH = "pyliteadmin.css"
    BINDINGS = [
        ("`", "toggle_dark", "Toggle dark mode"),
        ("c", "change_cursor", "Change cursor"),
        ("ctrl-c", "", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            TableSelector(id="table-selector"), id="table-selector-container"
        )
        yield Container(id="table")
        # Placeholder for future search feature
        # yield Container(TableSelector(id="table-selector2"),id="table-selector-container2")
        yield Footer()

    def change_table(self, table: str) -> None:
        """When a new table is selected, remove the old one and then add new one to the view"""
        new_table = TableViewer(table)

        try:
            self.query_one("TableViewer").remove()
        except:
            pass

        self.query_one("#table").mount(new_table)
        new_table.fixed_columns = len(new_table.columns)

        print(db_path)

    # When a table is selected from table selector
    def on_list_view_selected(self, list_item: ListItem) -> None:
        table = list_item.item.query_one("#label").renderable
        self.change_table(table)

    def action_change_cursor(self) -> None:
        self.query_one(DataTable).cursor_type = next(cursors)


app = PyLiteAdmin()
if __name__ == "__main__":
    app.run()
