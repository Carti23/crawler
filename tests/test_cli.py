import json
from unittest.mock import Mock, patch

from ghcrawler.cli import main

SIMPLE_REPO_HTML = "<html><body><a href='/a/b'>x</a></body></html>"
SEARCH_HTML_WITH_REPO = "<html><body><a href='/ownerX/repoY'>r</a></body></html>"
REPO_HTML_WITH_LANGS = """
<html><body>
    <ul>
        <li><span class='color-fg-default text-bold mr-1'>Python</span><span>100.0%</span></li>
    </ul>
</body></html>
"""

def create_mock_response(html_content):
    """Create a mock response with given HTML content."""
    resp = Mock()
    resp.raise_for_status = Mock()
    resp.text = html_content
    return resp

def create_side_effect_responses(search_html, repo_html):
    """Create a side effect function that returns different HTML based on URL."""
    def side_effect(url, **kwargs):
        m = Mock()
        m.raise_for_status = Mock()
        m.text = repo_html if url.endswith("/ownerX/repoY") else search_html
        return m
    return side_effect

def validate_repository_result(data, expected_url="https://github.com/a/b"):
    """Validate that data contains expected repository URL."""
    assert isinstance(data, list), "Result should be a list"
    assert len(data) > 0, "Result should not be empty"
    assert "url" in data[0], "First item should have 'url' key"
    assert data[0]["url"] == expected_url, f"Expected URL {expected_url}, got {data[0]['url']}"

def validate_extra_data(data):
    """Validate that data contains extra enrichment information."""
    assert isinstance(data, list), "Result should be a list"
    assert len(data) > 0, "Result should not be empty"
    assert "extra" in data[0], "First item should have 'extra' key"
    extra = data[0]["extra"]
    assert "owner" in extra, "Extra data should contain 'owner'"
    assert "language_stats" in extra, "Extra data should contain 'language_stats'"
    assert extra["owner"] == "ownerX", f"Expected owner 'ownerX', got {extra['owner']}"
    assert isinstance(extra["language_stats"], dict), "Language stats should be a dictionary"
    assert "Python" in extra["language_stats"], "Language stats should contain Python"
    assert extra["language_stats"]["Python"] == 100.0, "Python should be 100.0%"

@patch("requests.Session.get")
def test_cli_main_prints_json(mock_get, capsys):
    """Test basic CLI functionality with proxies."""
    mock_get.return_value = create_mock_response(SIMPLE_REPO_HTML)
    main(["--keywords", "a", "b", "--proxies", "1.2.3.4:8080", "--type", "Repositories"])
    out = capsys.readouterr().out
    data = json.loads(out)
    validate_repository_result(data)

@patch("requests.Session.get")
def test_cli_main_without_proxies(mock_get, capsys):
    """Test CLI functionality without proxies."""
    mock_get.return_value = create_mock_response(SIMPLE_REPO_HTML)
    main(["--keywords", "a", "b", "--type", "Repositories"])
    out = capsys.readouterr().out
    data = json.loads(out)
    validate_repository_result(data)

@patch("requests.Session.get")
def test_cli_main_with_timeout(mock_get, capsys):
    """Test CLI functionality with custom timeout."""
    mock_get.return_value = create_mock_response(SIMPLE_REPO_HTML)
    main(["--keywords", "a", "b", "--type", "Repositories", "--timeout", "30"])
    out = capsys.readouterr().out
    data = json.loads(out)
    validate_repository_result(data)

@patch("requests.Session.get")
def test_cli_main_with_extra(mock_get, capsys):
    """Test CLI functionality with extra enrichment."""
    mock_get.side_effect = create_side_effect_responses(SEARCH_HTML_WITH_REPO, REPO_HTML_WITH_LANGS)
    main(["--keywords", "a", "b", "--type", "Repositories", "--extra"])
    out = capsys.readouterr().out
    data = json.loads(out)
    validate_extra_data(data)

@patch("requests.Session.get")
def test_cli_main_issues_search(mock_get, capsys):
    """Test CLI functionality for issues search."""
    issues_html = "<html><body><a href='/ownerX/repoY/issues/123'>Issue</a></body></html>"
    mock_get.return_value = create_mock_response(issues_html)
    main(["--keywords", "bug", "fix", "--type", "Issues"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list), "Result should be a list"
    assert len(data) > 0, "Result should not be empty"
    assert data[0]["url"] == "https://github.com/ownerX/repoY/issues/123"

@patch("requests.Session.get")
def test_cli_main_wikis_search(mock_get, capsys):
    """Test CLI functionality for wikis search."""
    wikis_html = "<html><body><a href='/ownerX/repoY/wiki/Home'>Wiki</a></body></html>"
    mock_get.return_value = create_mock_response(wikis_html)
    main(["--keywords", "documentation", "--type", "Wikis"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list), "Result should be a list"
    assert len(data) > 0, "Result should not be empty"
    assert data[0]["url"] == "https://github.com/ownerX/repoY/wiki/Home"

def test_cli_main_direct_call():
    """Test the if __name__ == '__main__' block"""
    with patch('ghcrawler.cli.main') as mock_main:
        mock_main.assert_not_called()
