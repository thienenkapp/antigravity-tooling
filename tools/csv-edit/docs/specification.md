# `csv-edit` Application Specification

## Overview
`csv-edit` is a terminal-based (TUI) application written in Python that allows users to edit comma-separated values (CSV) files hosted directly on GitHub. 

Instead of cloning a repository, editing the file locally, committing, and pushing, `csv-edit` allows for a fluid, spreadsheet-like experience directly from the command line, and automatically handles the entire GitHub Pull Request creation workflow in the background.

## Core Features

1. **Spreadsheet-like TUI**
   - Built on the `Textual` library for a responsive, modern terminal UI.
   - Features a 2D data grid (using `DataTable`) with full keyboard navigation.
   - Inline cell editing via a prompted Input widget.

2. **Clipboard and Row Operations**
   - Single-cell copy and paste support.
   - **Copy Down**: Rapidly duplicate a cell's value into the cell immediately below it.
   - **Insert Row**: Append new blank rows to the bottom of the dataset.

3. **Direct GitHub Integration**
   - **Authentication**: Uses a Personal Access Token (`GITHUB_TOKEN` environment variable).
   - **URL Parsing**: Accepts standard GitHub web URLs (e.g., `https://github.com/owner/repo/blob/branch/path/to/data.csv`).
   - **Automated Workflow**:
     1. Fetches raw CSV data from the repository branch.
     2. Collects user edits in memory.
     3. On Save, prompts the user for a commit message.
     4. Creates a new unique branch (`csv-edit/update-<timestamp>`).
     5. Pushes the modified CSV as a commit to the new branch.
     6. Opens a Pull Request back to the original branch.

## Technical Requirements
- **Python**: `>= 3.9`
- **Dependencies**: 
  - `textual` (>= 0.52.1) - Manages the TUI rendering, layout, and event loop.
  - `PyGithub` (>= 2.1.1) - Wraps the GitHub REST API for fetching contents, creating branches, committing, and opening PRs.
- **Excluded Dependencies**: Purposely excludes heavy data dependencies (like `pandas`) to remain lightweight. CSV parsing is handled by the Python standard library's `csv` module.

## Key Bindings
| Key Sequence | Action | Description |
| ---- | ---- | ---- |
| `Enter` | Edit Cell | Opens the input field for the currently selected cell. Pressing `Enter` again commits the change. |
| `c` | Copy | Copies the value of the currently selected cell to the internal clipboard. |
| `v` | Paste | Pastes the value from the internal clipboard to the currently selected cell. |
| `d`| Copy Down | Copies the selected cell's value down one row, moving the cursor automatically. |
| `i` | Insert Row | Appends an empty row to the end of the data table. |
| `Ctrl+S` | Save to GitHub | Opens the commit message prompt and begins the Pull Request creation workflow. |
| `q` | Quit | Exits the application without saving. |
