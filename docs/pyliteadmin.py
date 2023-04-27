import os
from abc import ABC, abstractmethod
from itertools import cycle
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
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
    Input
)
import sqlite3
import db

# Set the table cursor to a cycle of three different cursor types
cursors = cycle(["column", "row", "cell"])

# Dict of keys and their related row values for currently viewed table
keys: dict[int, list] = {}

# Take command line argument for the path to the database
# If no command line argument is given, return error and exit
if len(os.sys.argv) > 1:
    db_path = os.sys.argv[1]
else:
    print("No database path given.\nUSAGE: pyliteadmin.py <path to database>")
 
    # Commented out for testing purposes
    # exit()
db_path=".\chinook.db"

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
    def get_table(self, table: str, search_column: str, search_value: str) -> tuple[list[tuple], list[str]]:
        print("searching where", search_column,"=", search_value, "on", table)
        return db.search_table(table, search_column = search_column, search_value = search_value)
        


class TableViewer(Widget):
    """A widget that displays the contents of a selected table"""
    def __init__(self, table: str, search_column: Optional[str] = None, search_value: Optional[str] = None, data_provider: TableDataProvider =  GetTable()) -> None:
        super().__init__()
        self.table = table
        self.data_provider = data_provider
        if search_column is not None:
            self.search_column = search_column
            self.search_term = search_value
            self.rows, self.columns = data_provider.get_table(f"{table}", search_column, search_value)
        else:
            self.rows, self.columns = data_provider.get_table(f"{table}")

    def compose(self) -> ComposeResult:
        yield DataTable(id="table")

    def on_mount(self) -> None:
        rows, columns = self.rows, self.columns
        data_table = self.query_one(DataTable)
        data_table.add_columns(*columns)
    
        #Iterate over each row and add it to the data table
        #Store the keys of each row in keys dict
        keys.clear()
        for row in rows:
            temp_key = data_table.add_row(*row)
            keys[temp_key] = row

        data_table.zebra_stripes = True
        data_table.cursor_type = "row"


class ConfirmAction(Widget):
    """A widget that allows the user to confirm an action"""

    def __init__(self, action: str) -> None:
        super().__init__()
        self.action = action
        self.confirmed = None
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "confirm-action-button":
            self.confirmed = True  
        elif button_id == "confirm-action-cancel":
            self.confirmed = False

    def compose(self) -> ComposeResult:
        yield Label(f"Are you sure you want to {self.action}?", id="confirm-action-label")
        yield Button(f"Confirm", id="confirm-action-button")
        yield Button(f"Cancel", id="confirm-action-cancel")


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

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
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
        ("ctrl+r", "refresh_table", "Refresh table"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(TableSelector(id="table-selector"), id="table-selector-container")
        yield Container(id="table-container")
        yield Container(id="search-container")
        yield Footer()

    def change_table(self, table: str, search: Optional[bool] = False) -> None:
        """When a new table is selected, remove the old one and then add new one to the view"""
        if search:
            search_column = self.query_one(TableSearch).search_column
            search_value = self.query_one(TableSearch).search_term
            new_table = TableViewer(table, search_column=search_column, search_value=search_value, data_provider=SearchTable())
        else:
            new_table = TableViewer(table,  data_provider=GetTable())
            new_search = TableSearch(table)

        try:
            self.query_one("TableViewer").remove()
        except:
            pass


        self.query_one("#table-container").mount(new_table)

        # If changing tables, change the search widget as well
        if 'new_search' in locals():
            try:
                self.query_one("TableSearch").remove()
            except:
                pass

            self.query_one("#search-container").mount(new_search)

        # Fixed_columns is a property of the DataTable widget, which is used to determine how many columns are fixed to the top of the screen 
        # (stay visible even when scrolling down)
        new_table.fixed_columns = len(new_table.columns)


    # When a table is selected from table selector
    def on_list_view_selected(self, list_item: ListItem) -> None:
        table = list_item.item.query_one("#label").renderable
        self.change_table(table)


    # Change cursor type
    def action_change_cursor(self) -> None:
        self.query_one(DataTable).cursor_type = next(cursors)


    # Delete a row
    def action_delete_row(self) -> None:
        if self.query_one(DataTable).cursor_type == "column":
            return

        table = self.query_one(DataTable)
        table_viewer = self.query_one(TableViewer)
        try:
            row_key, column_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        #TODO: Handle exception when cursor is not on a row
        except:
            return
        

        #TODO: Confirm delete
        #confirmationWindow = ConfirmAction(action="delete row")
        #self.mount(confirmationWindow)

        # Wait for user to confirm action
        #while confirmationWindow.confirmed == None:
            #yield

        #if confirmationWindow.confirmed:
        table.remove_row(row_key)

        
        db.delete_row(table_viewer.table, keys[row_key], table_viewer.columns)
        #confirmationWindow.remove()

    def on_button_pressed(self, event: Button.Pressed) -> None:
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
        try:
            self.change_table(self.query_one(TableViewer).table)
        except:
            return
    
    def action_quit(self) -> None:
        self.exit()
    


app = PyLiteAdmin()
if __name__ == "__main__":
    app.run()
