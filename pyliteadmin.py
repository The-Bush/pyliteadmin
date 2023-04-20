import os

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Header, Footer, DataTable, Static, ListView, ListItem, Label
import sqlite3
import db

table_names = db.get_table_names("./chinook.db")

class TableSelector(Widget):
    """A widget that allows the selection of a table from the selected database"""
    table = reactive("albums")
    
    def compose(self) -> ComposeResult:
        yield ListView(
            id="options")

    # On Mount, list all tables files in current working db
    def on_mount(self) -> None:
        table_names = db.get_table_names("./chinook.db")
        for table in table_names:
            new_listitem = ListItem(Label(table,id = "label"))
            self.query_one("#options").append(new_listitem)

    # When a table is selected from list
    def on_list_view_selected(self, list_item:ListItem) -> None:
        table = list_item.item.query_one("#label").renderable
        print(table)
class DBAdmin(App):
    """A terminal app to manage sqlite databases in a graphical interface"""
        
    def compose(self) -> ComposeResult:
        yield DataTable()
        yield Container(TableSelector(id="table-selector"))
        yield Footer()
    
    def on_mount(self) -> None:
        table = self.query_one("#table-selector").table
        rows, columns = db.get_table(f"{table}")
        data_table = self.query_one(DataTable)
        data_table.add_columns(*columns)
        data_table.add_rows(rows)

app = DBAdmin()
if __name__ == "__main__":
    app.run()
