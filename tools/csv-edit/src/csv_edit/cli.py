import argparse
import sys
from .tui import CSVEditorApp

def main():
    parser = argparse.ArgumentParser(description="Edit CSV files hosted on GitHub directly from your terminal.")
    parser.add_argument("url", help="GitHub URL to the CSV file (e.g., https://github.com/user/repo/blob/main/data.csv)")

    args = parser.parse_args()

    app = CSVEditorApp(github_url=args.url)
    app.run()

if __name__ == "__main__":
    main()
