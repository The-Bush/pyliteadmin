import os
from abc import ABC, abstractmethod
from itertools import cycle
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.reactive import reactive
from textual.message import Message, MessageTarget
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
    OptionList,
    Input,
)
from textual.screen import Screen, ModalScreen
import sqlite3
import db

# Set the table cursor to a cycle of three different cursor types
cursors = cycle(["row", "cell"])

# Dict of keys and their related row values for currently viewed table
keys: dict[int, list] = {}
# Dict of columns and  their related column values for currently viewed table  
column_keys: dict[str, str] = {}

# Take command line argument for the path to the database
# If no command line argument is given, return error and exit
if len(os.sys.argv) > 1:
    db_path = os.sys.argv[1]
else:
    print("No database path given.\nUSAGE: pyliteadmin.py <path to database>")

    # Commented out for testing purposes
    # exit()
db_path = ".\chinook.db"


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


# An abstract class for the different methods to fetch data from a table
class TableDataProvider(ABC):
    """An abstract class for the different methods to fetch data from a table"""

    @abstractmethod
    def get_table(self, table: str) -> tuple[list[tuple], list[str]]:
        pass


class GetTable(TableDataProvider):
    """A class that fetches all the table data"""

    def get_table(self, table: str) -> tuple[list[tuple], list[str]]:
        return db.get_table(table)


class SearchTable(TableDataProvider):
    """A class that searches for a table data"""

    def get_table(
        self, table: str, search_column: str, search_value: str
    ) -> tuple[list[tuple], list[str]]:
        print("searching where", search_column, "=", search_value, "on", table)
        return db.search_table(
            table, search_column=search_column, search_value=search_value
        )


class TableViewer(Widget):
    """A widget that displays the contents of a selected table"""

    def __init__(self, table: str, search_column: Optional[str] = None, search_value: Optional[str] = None, data_provider: TableDataProvider = GetTable(),) -> None:
        super().__init__()
        self.table = table
        self.data_provider = data_provider

        if search_column is not None:
            self.search_column = search_column
            self.search_term = search_value
            self.rows, self.columns = data_provider.get_table(
                f"{table}", search_column, search_value
            )
        else:
            self.rows, self.columns = data_provider.get_table(f"{table}")

    def compose(self) -> ComposeResult:
        yield DataTable(id="table")

    def on_mount(self) -> None:
        rows, columns = self.rows, self.columns
        data_table = self.query_one(DataTable)
        
        #data_table.add_columns(*columns)
        column_keys.clear()
        for i, column in enumerate(columns):
            temp_key = data_table.add_column(column, key = i)
            column_keys[temp_key] = column

        # Iterate over each row and add it to the data table
        # Store the keys of each row in keys dict
        keys.clear()
        for row in rows:
            temp_key = data_table.add_row(*row)
            keys[temp_key] = row

        # Set the table display to zebra stripes, and set default cursor type
        data_table.zebra_stripes = True

class ErrorMessageModal(ModalScreen):
    """A widget that displays an error message"""

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(f"{self.message}", id="error-message-label"),
            Button(f"OK", id="error-message-ok"),
            id="error-message-grid",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "error-message-ok":
            self.app.pop_screen()

class ConfirmEditCell(ModalScreen):
    """A widget that allows the user to update a cell's contents"""
    def __init__(self, table_viewer:TableViewer, row_key: int, column_key, value) -> None:
        super().__init__()
        self.table_viewer = table_viewer
        self.row_key = row_key
        self.column_key = column_key
        #TODO: Get this value correct, as it can't work without it.
        self.column = column_keys[column_key]
        self.value = value

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(f"Enter the cell's new value:", id="edit-cell-label"),
            Input(value=f"{self.value}", id="edit-cell-input"),
            Button(f"Confirm", id="confirm-edit-cell-button"),
            Button(f"Cancel", id="confirm-edit-cell-cancel"),
            id="confirm-action-grid",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "confirm-edit-cell-button":
            try:
                # Update the db
                db.update_cell(
                table=self.table_viewer.table, 
                row=keys[self.row_key], 
                column=self.column,
                columns=self.table_viewer.columns,
                new_value=self.value,
                )
            except Exception as error:
                self.app.pop_screen()
                self.app.push_screen(ErrorMessageModal(error))
                return
            
            # Update the table viewer
            self.table_viewer.query_one(DataTable).update_cell(self.row_key, self.column_key, self.value)
            self.app.pop_screen()

        elif button_id == "confirm-edit-cell-cancel":
            self.app.pop_screen()

    # When anything is typed into the input, update the stored value
    def on_input_changed(self, event: Input.Changed) -> None:
        self.value = event.input.value

class ConfirmDeleteRow(ModalScreen):
    """A widget that allows the user to confirm an action"""

    def __init__(self, table_viewer:TableViewer, row_key: int, columns: list[str]) -> None:
        super().__init__()
        self.table_viewer = table_viewer
        self.row_key = row_key
        self.columns = columns

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "confirm-action-button":
            db.delete_row(self.table_viewer.table, keys[self.row_key], self.table_viewer.columns)
            self.table_viewer.query_one(DataTable).remove_row(self.row_key)
            self.app.pop_screen()
        elif button_id == "confirm-action-cancel":
            self.confirmed = False
            self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(
                f"Are you sure you want to delete this row?", id="confirm-action-label"
            ),
            Static(f"{keys[self.row_key]}", id="confirm-action-row"),
            Button(f"Confirm", id="confirm-action-button"),
            Button(f"Cancel", id="confirm-action-cancel"),
            id="confirm-action-grid",
        )


class TableSearch(Widget):
    """A widget that allows the searching within a table"""

    def __init__(self, table: str) -> None:
        super().__init__()
        self.table = table
        self.search_column = ""
        self.search_term = ""

    def compose(self) -> ComposeResult:
        yield Label("Search Column", id="search-label")
        yield OptionList(id="search-column-options")
        yield Label("Search Term", id="search-term-label")
        yield Input(id="search-input")
        yield Button("Search", id="search-button", variant="primary")

    def on_mount(self) -> None:
        table = self.table
        columns = db.get_columns(table)
        for column in columns:
            self.query_one(OptionList).add_option(column)

        # Disable search button by default
        self.query_one("#search-button").disabled = True

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        self.search_column = event.option.prompt
        self.check_button()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.search_term = event.input.value
        self.check_button()

    def check_button(self) -> None:
        if self.search_term == "" or self.search_column == "":
            self.query_one("#search-button").disabled = True
        else:
            self.query_one("#search-button").disabled = False


class PyLiteAdmin(App):
    """A terminal app to manage sqlite databases in a terminal interface"""

    CSS_PATH = "pyliteadmin.css"
    BINDINGS = [
        ("`", "toggle_dark", "Toggle dark mode"),
        ("c", "change_cursor", "Change cursor"),
        ("d", "delete_row", "Delete row"),
        ("e", "edit_cell", "Edit cell"),
        ("ctrl+r", "refresh_table", "Refresh table"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            TableSelector(id="table-selector"), id="table-selector-container")
        yield Container(id="table-container")
        yield Container(id="search-container")
        yield Footer()

    def change_table(self, table: str, search: Optional[bool] = False) -> None:
        """When a new table is selected, remove the old one and then add new one to the view"""
        if search:
            search_column = self.query_one(TableSearch).search_column
            search_value = self.query_one(TableSearch).search_term
            new_table = TableViewer(
                table,
                search_column=search_column,
                search_value=search_value,
                data_provider=SearchTable(),
            )
        else:
            new_table = TableViewer(table, data_provider=GetTable())
            new_search = TableSearch(table)

        try:
            self.query_one("TableViewer").remove()
        except:
            pass

        self.query_one("#table-container").mount(new_table)

        # If changing tables, change the search widget as well
        if "new_search" in locals():
            try:
                self.query_one("TableSearch").remove()
            except:
                pass

            self.query_one("#search-container").mount(new_search)

        # Fixed_columns is a property of the DataTable widget, which is used to determine how many columns are fixed to the top of the screen
        # (stay visible even when scrolling down)
        new_table.fixed_columns = len(new_table.columns)

    def on_list_view_selected(self, list_item: ListItem) -> None:
        """Change table when a new one is selected from the table selector"""
        table = list_item.item.query_one("#label").renderable
        self.change_table(table)

    def action_change_cursor(self) -> None:
        """Change cursor type"""
        self.query_one(DataTable).cursor_type = next(cursors)

    def action_delete_row(self) -> None:
        """When a row is deleted, remove it from the database and the data table"""
        if self.query_one(DataTable).cursor_type == "column":
            return

        table = self.query_one(DataTable)
        table_viewer = self.query_one(TableViewer)

        # Handle exception when cursor is not on a row
        try:
            row_key, column_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        except:
            return
        
        # Confirm delete
        self.app.push_screen(ConfirmDeleteRow(table_viewer, row_key, table.columns))

    def action_edit_cell(self) -> None:
        """When a cell is updated, update the database and the data table"""
        table = self.query_one(DataTable)
        table_viewer = self.query_one(TableViewer)

        # Handle exception when cursor is not on a row
        try:
            row_key, column_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        except:
            return

        value = table.get_cell(row_key, column_key)
        # Confirm update
        self.app.push_screen(ConfirmEditCell(
            table_viewer=table_viewer, 
            row_key=row_key, 
            column_key=column_key, 
            value=value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """When the search button is pressed, change table to a new table with the search results"""
        button_id = event.button.id
        if button_id == "search-button":
            # Handle when no column is selected
            if self.query_one(TableSearch).search_column == None:
                return

            # Handle when no input present
            if self.query_one(TableSearch).search_term == None:
                return

            self.change_table(self.query_one(TableViewer).table, search=True)
            return

    def action_refresh_table(self) -> None:
        """Refresh current table to fetch new rows or go back to whole-table view"""
        try:
            self.change_table(self.query_one(TableViewer).table)
        except:
            return

    def action_quit(self) -> None:
        self.exit()


app = PyLiteAdmin()
if __name__ == "__main__":
    app.run()
