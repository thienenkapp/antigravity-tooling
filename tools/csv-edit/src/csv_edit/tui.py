import csv
import io
import time
from typing import List, Optional
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Input
from textual.containers import Container
from textual.binding import Binding
from textual import work
from textual.coordinate import Coordinate
from .github_client import GitHubClient

class CSVEditorApp(App):
    """A Textual app to edit CSV files from GitHub."""

    CSS = """
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+s", "save", "Save to GitHub", show=True),
        Binding("c", "copy_cell", "Copy", show=True),
        Binding("v", "paste_cell", "Paste", show=True),
        Binding("d", "copy_down", "Copy Down", show=True),
        Binding("i", "insert_row", "Insert Row", show=True),
    ]

    def __init__(self, github_url: str):
        super().__init__()
        self.github_url = github_url
        self.github_client = GitHubClient()
        self.original_csv_content = ""
        self.csv_headers: List[str] = []

        # Clipboard buffer
        self._copied_cell_value: Optional[str] = None
        self._editing_coordinate: Optional[Coordinate] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield DataTable(cursor_type="cell")

        # Hidden input for editing cells
        edit_input = Input(id="cell-editor")
        edit_input.display = False
        yield edit_input

        # Hidden input for commit messages
        commit_input = Input(id="commit-editor", placeholder="Enter commit message... (Press Enter to save)")
        commit_input.display = False
        yield commit_input

        yield Footer()

    async def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "csv-edit"
        self.sub_title = self.github_url

        # Load the data
        try:
            content, _ = self.github_client.fetch_csv(self.github_url)
            self.original_csv_content = content
            self.load_csv(content)
        except Exception as e:
            self.notify(f"Error loading CSV: {e}", title="Error", severity="error")

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """When a cell is selected, show the input field to edit it."""
        table = self.query_one(DataTable)
        editor = self.query_one("#cell-editor", Input)

        # Get current value
        current_value = table.get_cell_at(event.coordinate)

        # Position the editor (in a real app we might float it, but for now we put it at the bottom focus)
        editor.value = str(current_value)
        editor.display = True
        editor.focus()

        # Store where we are editing
        self._editing_coordinate = event.coordinate

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """When the user presses Enter in an input field."""
        if event.input.id == "cell-editor" and hasattr(self, "_editing_coordinate"):
            table = self.query_one(DataTable)
            table.update_cell_at(self._editing_coordinate, event.value, update_width=True)

            # Hide editor and focus back to table
            event.input.display = False
            table.focus()
        elif event.input.id == "commit-editor":
            # Start the save process with the message
            commit_message = event.value.strip() or "Update CSV via csv-edit TUI"
            event.input.display = False
            self.query_one(DataTable).focus()
            self._execute_save(commit_message)

    def load_csv(self, content: str) -> None:
        """Parse CSV content and load it into the DataTable."""
        table = self.query_one(DataTable)
        table.clear(columns=True)

        reader = csv.reader(io.StringIO(content))

        try:
            headers = next(reader)
            self.csv_headers = headers
            table.add_columns(*headers)

            for row in reader:
                # Ensure row has same length as headers
                padded_row = list(row) + [""] * (len(headers) - len(row))
                padded_row = padded_row[:len(headers)]
                table.add_row(*padded_row)

        except StopIteration:
            self.notify("The CSV file is empty.", severity="warning")

    def dump_csv(self) -> str:
        """Convert the DataTable back into a CSV string."""
        table = self.query_one(DataTable)

        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(self.csv_headers)

        # Write all rows
        for row_key in table.rows:
            row_data = table.get_row(row_key)
            writer.writerow(row_data)

        return output.getvalue()

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

    def action_copy_down(self) -> None:
        """Copy the value of the currently selected cell to the cell immediately below it."""
        table = self.query_one(DataTable)
        coord = table.cursor_coordinate
        if coord is not None:
            # Check if there is a row below
            if coord.row < len(table.rows) - 1:
                val = table.get_cell_at(coord)
                target_coord = Coordinate(row=coord.row + 1, column=coord.column)
                table.update_cell_at(target_coord, val, update_width=True)
                table.move_cursor(row=coord.row + 1, column=coord.column)
                self.notify("Copied down")
            else:
                self.notify("Make a new row first (press 'i')")

    def action_insert_row(self) -> None:
        """Insert an empty row below the current cursor."""
        table = self.query_one(DataTable)
        coord = table.cursor_coordinate

        empty_row = [""] * len(self.csv_headers)

        if coord is not None:
             # Textual's DataTable doesn't have an insert_row(index) easily.
             # We might have to clear and rebuild, or append at the end.
             # For simplicity now, let's append at the end.
             # A proper insert might require reconstructing the table lines.
             table.add_row(*empty_row)
             # Move to the new row
             table.move_cursor(row=len(table.rows) - 1)
             self.notify("Appended new empty row at the bottom.")
        else:
             table.add_row(*empty_row)

    def action_save(self) -> None:
        """Prompt the user for a commit message before saving."""
        editor = self.query_one("#commit-editor", Input)
        editor.value = "Update CSV via csv-edit TUI" # Default message
        editor.display = True
        editor.focus()

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
            self.call_from_thread(self.notify, f"Successfully created PR:\n{pr_url}", title="Saved", severity="information")
        except Exception as e:
            self.call_from_thread(self.notify, f"Error saving to GitHub: {e}", title="Error", severity="error")
