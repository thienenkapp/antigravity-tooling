# Antigravity Tooling

Welcome to `antigravity-tooling`! This repository is designed as a **Monorepo** to house a collection of professional, scalable Python utility tools and automated workflows.

## The Monorepo Strategy

To maintain clean codebases and prevent dependency conflicts, this repository uses an isolated packaging architecture:

1. **Isolated Applications**: All individual tools live within the `tools/` directory. Each tool acts as an independent Python package with its own source (`src/`), testing suite (`tests/`), and dependency management (`pyproject.toml`).
2. **Global Automation**: While tools remain isolated, automation is global. The `.agents/workflows/` directory contains standard operating procedures (SOPs) that our AI Agent (Antigravity) natively understands. For example, triggering a global test workflow automatically cycles through and tests every tool in the repository seamlessly.

## Repository Structure

```text
antigravity-tooling/
├── tools/                      # The core applications
│   ├── csv-edit/               # A Textual-based terminal CSV editor with GitHub PR integration
│   └── [future-tools]          
│
├── .agents/workflows/          # Antigravity Global Workflows
│   └── run-tests.md            # Automates `pytest` across all tools
│
├── .gitignore                  
└── README.md
```

## Included Tools

### [csv-edit](./tools/csv-edit/docs/specification.md)
A fully-featured TUI (Terminal User Interface) spreadsheet application built with `Textual`. It allows for direct manipulation of CSV files hosted remotely on GitHub, including operations like cell editing, magic copy-down, and row insertions. Instead of committing locally, `csv-edit` automatically authenticates with the GitHub API, spins up a new branch, and handles Pull Request generation natively from the terminal. 

> *See [the csv-edit specifications](./tools/csv-edit/docs/specification.md) for full commands and installation instructions.*

## Getting Started

Because the tools are decoupled, you must install the specific tool you want to work on locally:

```bash
# Navigate to the specific tool you want to install
cd tools/csv-edit

# Install the tool and its developer dependencies 
pip install -e ".[dev]"
```

## Running Global Tests

You can run automated tests for the entire monorepo either manually using the bash script, or by simply asking the Antigravity assistant:
> *"Run the tests workflow!"*
