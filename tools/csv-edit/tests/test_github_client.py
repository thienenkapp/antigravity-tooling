import pytest
from csv_edit.github_client import GitHubClient

def test_parse_url_valid():
    """Test that valid GitHub URLs are correctly parsed."""
    client = GitHubClient(token="dummy")
    result = client.parse_url("https://github.com/owner/repo/blob/main/data/file.csv")
    
    assert result["owner"] == "owner"
    assert result["repo"] == "repo"
    assert result["branch"] == "main"
    assert result["file_path"] == "data/file.csv"

def test_parse_url_invalid():
    """Test that invalid URLs raise a ValueError."""
    client = GitHubClient(token="dummy")
    with pytest.raises(ValueError):
        client.parse_url("https://github.com/owner/repo/tree/main")
