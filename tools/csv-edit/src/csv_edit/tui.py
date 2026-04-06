import csv
import io
import time
from typing import List, Optional, Any
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Input
from textual.containers import Container
from textual.binding import Binding
from textual import work
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from .github_client import GitHubClient

class InputModal(ModalScreen[Optional[str]]):
    """An isolated dialog screen exclusively for taking string inputs."""
    
    DEFAULT_CSS = """
    InputModal {
        align: center middle;
        background: $background 50%;
    }
    InputModal > Input {
        width: 60%;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        # Textual Inputs natively capture Enter to submit, but we list it in BINDINGS for the Footer visual
        Binding("enter", "submit", "Confirm / Submit"), 
    ]

    def __init__(self, placeholder: str = "", initial_value: str = ""):
        super().__init__()
        self.placeholder = placeholder
        self.initial_value = initial_value

    def compose(self) -> ComposeResult:
        yield Input(value=self.initial_value, placeholder=self.placeholder)

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)

class CSVEditorApp(App):
    """A Textual app to edit CSV files from GitHub."""

    CSS = """
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+s", "save", "Save/ Commit to GitHub and quit.", show=True),
        Binding("c", "copy_cell", "Copy cell", show=True),
        Binding("v", "paste_cell", "Paste cell", show=True),
        Binding("C", "copy_row", "Copy row", show=True),
        Binding("V", "paste_row", "Paste row", show=True),
        Binding("d", "copy_down", "Copy Down", show=True),
        Binding("D", "delete_row", "Delete row", show=True),
        Binding("i", "insert_row", "Insert row after", show=True),
        Binding("I", "insert_column", "Insert column after", show=True),
        Binding("a", "append_row", "Append row", show=True),
        Binding("A", "append_column", "Append column", show=True),
    ]

    def __init__(self, github_url: str):
        super().__init__()
        self.github_url = github_url
        self.github_client = GitHubClient()
        self.original_csv_content = ""
        self.csv_headers: List[str] = []
        
        # Clipboard buffers
        self._copied_cell_value: Optional[str] = None
        self._copied_row_value: Optional[List[str]] = None
        self._editing_coordinate: Optional[Coordinate] = None
        
        # Output artifacts
        self.pr_url: Optional[str] = None
        self.branch_name: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield DataTable(cursor_type="cell", show_row_labels=True)
        yield Footer()

    async def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "csv-edit"
        self.sub_title = self.github_url
        
        try:
            content, _ = self.github_client.fetch_csv(self.github_url)
            self.original_csv_content = content
            self.load_csv(content)
        except Exception as e:
            self.notify(f"Error loading CSV: {e}", title="Error", severity="error")

    def rebuild_table(self, headers: List[str], rows: List[List[str]]) -> None:
        """Completely rebuilds the DataTable using the provided grid, adding line labels."""
        table = self.query_one(DataTable)
        table.clear(columns=True)
        self.csv_headers = headers
        table.add_columns(*headers)
        
        for i, row in enumerate(rows):
            # Pad the row if it's too short
            padded_row = list(row) + [""] * (len(headers) - len(row))
            padded_row = padded_row[:len(headers)]
            table.add_row(*padded_row, label=str(i + 1))

    def _get_current_grid_state(self) -> List[List[str]]:
        """Extracts the entire data table contents into a generic 2D python list."""
        table = self.query_one(DataTable)
        grid = []
        for row_key in table.rows:
            grid.append(list(table.get_row(row_key)))
        return grid

    def load_csv(self, content: str) -> None:
        """Parse CSV content and layout."""
        reader = csv.reader(io.StringIO(content))
        try:
            headers = next(reader)
            rows = [list(row) for row in reader]
            self.rebuild_table(headers, rows)
        except StopIteration:
            self.notify("The CSV file is empty.", severity="warning")

    def dump_csv(self) -> str:
        """Convert the DataTable back into a CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.csv_headers)
        
        for row in self._get_current_grid_state():
            writer.writerow(row)
            
        return output.getvalue()
        
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """When a cell is selected, show the input dialog to edit it."""
        table = self.query_one(DataTable)
        current_value = table.get_cell_at(event.coordinate)
        
        def save_cell(new_value: Optional[str]) -> None:
            if new_value is not None:
                table.update_cell_at(event.coordinate, new_value, update_width=True)
                
        self.push_screen(InputModal(initial_value=str(current_value)), save_cell)

    # --- Actions ---
    
    def action_copy_cell(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_coordinate:
            self._copied_cell_value = str(table.get_cell_at(table.cursor_coordinate))
            self.notify(f"Copied: {self._copied_cell_value}")

    def action_paste_cell(self) -> None:
        if self._copied_cell_value is not None:
            table = self.query_one(DataTable)
            if table.cursor_coordinate:
                table.update_cell_at(table.cursor_coordinate, self._copied_cell_value, update_width=True)
                self.notify(f"Pasted: {self._copied_cell_value}")

    def action_copy_row(self) -> None:
        table = self.query_one(DataTable)
        coord = table.cursor_coordinate
        if coord is not None:
            # Reconstruct the true row
            idx = coord.row
            grid = self._get_current_grid_state()
            self._copied_row_value = list(grid[idx])
            self.notify(f"Copied row {idx + 1}")

    def action_paste_row(self) -> None:
        if self._copied_row_value is not None:
            table = self.query_one(DataTable)
            coord = table.cursor_coordinate
            if coord is not None:
                idx = coord.row
                # Since pasting a row replaces elements, iterate across the row and update cell by cell
                for col_idx, val in enumerate(self._copied_row_value):
                    if col_idx < len(self.csv_headers):
                        c = Coordinate(row=idx, column=col_idx)
                        table.update_cell_at(c, val, update_width=True)
                self.notify(f"Pasted into row {idx + 1}")

    def action_delete_row(self) -> None:
        table = self.query_one(DataTable)
        coord = table.cursor_coordinate
        if coord is not None:
            grid = self._get_current_grid_state()
            if len(grid) > 1: # Let's prevent deleting the very last row for safety
                del grid[coord.row]
                self.rebuild_table(self.csv_headers, grid)
                self.notify("Deleted row")
            else:
                self.notify("Cannot delete the only row.", severity="warning")

    def action_copy_down(self) -> None:
        table = self.query_one(DataTable)
        coord = table.cursor_coordinate
        if coord is not None:
            if coord.row < len(table.rows) - 1:
                val = table.get_cell_at(coord)
                target_coord = Coordinate(row=coord.row + 1, column=coord.column)
                table.update_cell_at(target_coord, val, update_width=True)
                table.move_cursor(row=coord.row + 1, column=coord.column)
                self.notify("Copied down")
            else:
                self.notify("Make a new row first")

    def action_insert_row(self) -> None:
        """Insert an empty row immediately after the current cursor."""
        table = self.query_one(DataTable)
        coord = table.cursor_coordinate
        
        empty_row = [""] * len(self.csv_headers)
        grid = self._get_current_grid_state()
        
        if coord is not None:
             insert_idx = coord.row + 1
             grid.insert(insert_idx, empty_row)
             self.rebuild_table(self.csv_headers, grid)
             table.move_cursor(row=insert_idx)
             self.notify("Inserted row")
        else:
             grid.append(empty_row)
             self.rebuild_table(self.csv_headers, grid)

    def action_append_row(self) -> None:
        """Append a new row to the very bottom."""
        table = self.query_one(DataTable)
        empty_row = [""] * len(self.csv_headers)
        
        # We can optimize this by not rebuilding the whole table 
        table.add_row(*empty_row, label=str(len(table.rows) + 1))
        table.move_cursor(row=len(table.rows) - 1)
        self.notify("Appended row")
        
    def action_insert_column(self) -> None:
        """Prompt to splice a column at the current cursor."""
        def handle_col_name(col_name: Optional[str]) -> None:
            if col_name is not None:
                col_name = col_name.strip() or f"Column {len(self.csv_headers) + 1}"
                table = self.query_one(DataTable)
                insert_idx = table.cursor_coordinate.column + 1 if table.cursor_coordinate else len(self.csv_headers)
                
                headers = list(self.csv_headers)
                headers.insert(insert_idx, col_name)
                
                grid = self._get_current_grid_state()
                for row in grid:
                    row.insert(insert_idx, "")
                    
                self.rebuild_table(headers, grid)
                if table.cursor_coordinate:
                    table.move_cursor(row=table.cursor_coordinate.row, column=insert_idx)
                table.focus()
                self.notify(f"Inserted column: {col_name}")
                
        self.push_screen(InputModal(placeholder="Enter new column name..."), handle_col_name)

    def action_append_column(self) -> None:
        """Prompt to append a column directly to the end."""
        table = self.query_one(DataTable)
        if len(table.columns) > 0:
            table.move_cursor(column=len(table.columns) - 1)
            
        self.action_insert_column()

    def action_save(self) -> None:
        """Prompt the user for a commit message before saving."""
        def handle_commit(commit_message: Optional[str]) -> None:
            if commit_message is not None:
                commit_message = commit_message.strip() or "Update CSV via csv-edit TUI"
                self._execute_save(commit_message)
                
        self.push_screen(InputModal(placeholder="Enter commit message..."), handle_commit)

    @work(thread=True)
    def _execute_save(self, commit_msg: str) -> None:
        """Save the current table data back to GitHub with a custom message."""
        self.notify("Starting Save to GitHub...", title="Saving")
        new_content = self.dump_csv()
        
        branch_name = f"csv-edit/update-{int(time.time())}"
        
        try:
            pr_url = self.github_client.create_pr_with_changes(
                self.github_url, new_content, commit_msg, branch_name
            )
            
            # Store values so CLI can print them on exit
            self.pr_url = pr_url
            self.branch_name = branch_name
            
            self.call_from_thread(self.notify, f"Successfully created PR:\n{pr_url}", title="Saved", severity="information")
            time.sleep(1)
            self.call_from_thread(self.exit)
        except Exception as e:
            self.call_from_thread(self.notify, f"Error saving to GitHub: {e}", title="Error", severity="error")
