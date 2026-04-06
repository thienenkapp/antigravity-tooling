# csv-edit

A blazing-fast, terminal-based CSV editor allowing you to make spreadsheet-like edits to CSV files hosted directly on GitHub without ever leaving your terminal or manually managing git branches.

## Why `csv-edit`?
Usually, editing a data file on GitHub requires you to:
1. Clone the repository.
2. Open Excel or a heavy text editor.
3. Make changes, save, and stage.
4. Commit, push to a new branch, and create a Pull Request on the web UI.

`csv-edit` simplifies this into a single step. Run the command, edit the cells directly using hotkeys, and hit Save. The application handles branching and creating the PR automatically via the GitHub API.

## Installation

Ensure you have a recent version of Python (>= 3.9) and install it from the tools directory:

```bash
cd tools/csv-edit
pip install -e ".[dev]"
```

*Note: You must set the `GITHUB_TOKEN` environment variable to a valid Personal Access Token before running.*
```bash
export GITHUB_TOKEN="your_token_here"
```

## Usage

Simply pass the web URL of the target CSV file hosted on GitHub:
```bash
csv-edit "https://github.com/owner/repository/blob/main/data.csv"
```

## Hotkeys

| Key | Action |
|---|---|
| `Enter` | Edit the currently selected cell |
| `c` | Copy the selected cell |
| `v` | Paste the copied value to the active cell |
| `d` | Copy Down (duplicates the cell to the row immediately below it) |
| `i` | Insert an empty row at the bottom of the dataset |
| `I` | Insert a new column (Prompts for the column name) |
| `Ctrl+S` | Save/ Commit to GitHub and quit. Prompts for a commit message, pushes the PR, and exits. |
| `q` | Quit without saving. |
