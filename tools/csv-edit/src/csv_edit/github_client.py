import os
import re
from typing import Tuple, Dict, Any, Optional
from github import Github, Auth
from github.Repository import Repository


class GitHubClient:
    """Handles parsing GitHub URLs and interacting with the GitHub API."""

    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.

        If no token is provided, it tries to read the GITHUB_TOKEN environment variable.
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token is required. Please set the GITHUB_TOKEN environment variable."
            )

        auth = Auth.Token(self.token)
        self.gh = Github(auth=auth)

    @staticmethod
    def parse_url(url: str) -> Dict[str, str]:
        """Parses a GitHub URL into its components.

        Expected format: https://github.com/owner/repo/blob/branch/path/to/file.csv
        """
        # Remove trailing slashes and common prefixes
        url = url.strip("/")
        if url.startswith("https://github.com/"):
            url = url[len("https://github.com/"):]

        parts = url.split("/")
        if len(parts) < 5 or parts[2] != "blob":
            raise ValueError(f"Invalid GitHub object URL: {url}")

        owner = parts[0]
        repo = parts[1]
        branch = parts[3]
        file_path = "/".join(parts[4:])

        return {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "file_path": file_path
        }

    def get_repo(self, owner: str, repo: str) -> Repository:
        return self.gh.get_repo(f"{owner}/{repo}")

    def fetch_csv(self, url: str) -> Tuple[str, str]:
        """Fetches the CSV content from a GitHub URL.

        Returns:
            Tuple containing (file_content_as_string, file_sha)
        """
        parsed = self.parse_url(url)
        repo = self.get_repo(parsed["owner"], parsed["repo"])

        # Get the file contents
        file_content = repo.get_contents(parsed["file_path"], ref=parsed["branch"])

        # PyGithub returns a single ContentFile or a list (if it's a dir).
        # We assume it's a single file since it's a CSV.
        if isinstance(file_content, list):
             raise ValueError(f"URL points to a directory, not a file: {url}")

        # Decode the content (often base64 encoded by GitHub)
        decoded_content = file_content.decoded_content.decode("utf-8")

        return decoded_content, file_content.sha

    def create_pr_with_changes(self, url: str, new_content: str, commit_message: str, branch_name: str) -> str:
        """Pushes new content to a new branch and opens a regular PR.

        Returns:
            The URL of the created Pull Request.
        """
        parsed = self.parse_url(url)
        repo = self.get_repo(parsed["owner"], parsed["repo"])
        base_branch_name = parsed["branch"]

        # 1. Get the base branch Ref to find the latest commit SHA
        base_ref = repo.get_git_ref(f"heads/{base_branch_name}")

        # 2. Create a new branch pointing to the same commit
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)

        # 3. Get the current file SHA to perform the update
        file_content = repo.get_contents(parsed["file_path"], ref=base_branch_name)
        if isinstance(file_content, list):
             raise ValueError(f"URL points to a directory, not a file: {url}")

        # 4. Update the file on the NEW branch
        repo.update_file(
            path=parsed["file_path"],
            message=commit_message,
            content=new_content,
            sha=file_content.sha,
            branch=branch_name
        )

        # 5. Create the Pull Request
        pr = repo.create_pull(
            title=commit_message,
            body="Updated CSV file via `csv-edit` TUI.",
            head=branch_name,
            base=base_branch_name
        )

        return pr.html_url
