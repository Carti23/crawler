from bs4 import BeautifulSoup

from ghcrawler.parsers import (
    _extract_github_links,
    extract_search_urls,
    parse_language_stats,
)

SIMPLE_REPO_HTML = """
<html>
    <body>
        <a href="/user1/repo1">Repo 1</a>
        <a href="https://github.com/user2/repo2">Repo 2</a>
        <a href="//external.com">External</a>
        <a href="/user3/repo3#section">Repo 3</a>
        <a href="/user4/repo4?param=value">Repo 4</a>
    </body>
</html>
"""

REPOSITORIES_HTML = """
<html>
    <body>
        <a href="/features/copilot">Feature</a>
        <a href="/topics/python">Topic</a>
        <a href="/user1/repo1">Valid Repo</a>
        <a href="/search/advanced">Search</a>
        <a href="/user2/repo2">Another Repo</a>
    </body>
</html>
"""

ISSUES_HTML = """
<html>
    <body>
        <a href="/user1/repo1/issues/123">Issue 1</a>
        <a href="/user2/repo2/issues/456">Issue 2</a>
        <a href="/user3/repo3/issues">Issues page</a>
        <a href="/user4/repo4/issues/789/pull">Pull request</a>
    </body>
</html>
"""

WIKIS_HTML = """
<html>
    <body>
        <a href="/user1/repo1/wiki/Home">Wiki Home</a>
        <a href="/user2/repo2/wiki/Getting-Started">Wiki Page</a>
        <a href="/user3/repo3/wiki">Wiki index</a>
    </body>
</html>
"""

LANGUAGE_STATS_HTML = """
<html>
    <body>
        <ul>
            <li>
                <span class="color-fg-default text-bold mr-1">Python</span>
                <span>60.0%</span>
            </li>
            <li>
                <span class="color-fg-default text-bold mr-1">JavaScript</span>
                <span>40.0%</span>
            </li>
        </ul>
    </body>
</html>
"""

def create_soup(html):
    """Create BeautifulSoup object from HTML string."""
    return BeautifulSoup(html, "html.parser")

def validate_urls(urls, expected_urls):
    """Validate that URLs match expected results exactly."""
    assert set(urls) == set(expected_urls), f"Expected {expected_urls}, got {urls}"

def validate_language_stats(stats, expected_stats):
    """Validate that language statistics match expected results."""
    assert stats == expected_stats, f"Expected {expected_stats}, got {stats}"

def test_abs_github_links():
    """Test _abs_github_links function."""
    soup = create_soup(SIMPLE_REPO_HTML)
    links = _extract_github_links(soup)
    
    expected = [
        "https://github.com/user1/repo1",
        "https://github.com/user2/repo2", 
        "https://github.com/user3/repo3",
        "https://github.com/user4/repo4"
    ]
    
    validate_urls(links, expected)

def test_extract_search_urls_repositories():
    """Test repository URL extraction."""
    urls = extract_search_urls(REPOSITORIES_HTML, "Repositories")
    expected = [
        "https://github.com/user1/repo1",
        "https://github.com/user2/repo2"
    ]
    validate_urls(urls, expected)

def test_extract_search_urls_issues():
    """Test issues URL extraction."""
    urls = extract_search_urls(ISSUES_HTML, "Issues")
    expected = [
        "https://github.com/user1/repo1/issues/123",
        "https://github.com/user2/repo2/issues/456",
        "https://github.com/user4/repo4/issues/789"
    ]
    validate_urls(urls, expected)

def test_extract_search_urls_wikis():
    """Test wikis URL extraction."""
    urls = extract_search_urls(WIKIS_HTML, "Wikis")
    expected = [
        "https://github.com/user1/repo1/wiki/Home",
        "https://github.com/user2/repo2/wiki/Getting-Started"
    ]
    validate_urls(urls, expected)

def test_parse_language_stats_basic():
    """Test basic language stats parsing."""
    stats = parse_language_stats(LANGUAGE_STATS_HTML)
    expected = {"Python": 60.0, "JavaScript": 40.0}
    validate_language_stats(stats, expected)

def test_parse_language_stats_with_regex():
    """Test language stats parsing with regex fallback."""
    html = """
    <html>
        <body>
            <ul>
                <li>
                    <span class="color-fg-default text-bold mr-1">Python</span>
                    Some text 75.5% more text
                </li>
            </ul>
        </body>
    </html>
    """
    stats = parse_language_stats(html)
    expected = {"Python": 100.0}
    validate_language_stats(stats, expected)

def test_parse_language_stats_invalid_percentage():
    """Test language stats with invalid percentage values."""
    html = """
    <html>
        <body>
            <ul>
                <li>
                    <span class="color-fg-default text-bold mr-1">Python</span>
                    <span>invalid%</span>
                </li>
                <li>
                    <span class="color-fg-default text-bold mr-1">JavaScript</span>
                    <span>150.0%</span>
                </li>
            </ul>
        </body>
    </html>
    """
    stats = parse_language_stats(html)
    expected = {}
    validate_language_stats(stats, expected)

def test_parse_language_stats_normalization():
    """Test language stats normalization."""
    html = """
    <html>
        <body>
            <ul>
                <li>
                    <span class="color-fg-default text-bold mr-1">Python</span>
                    <span>50.0%</span>
                </li>
                <li>
                    <span class="color-fg-default text-bold mr-1">JavaScript</span>
                    <span>50.0%</span>
                </li>
            </ul>
        </body>
    </html>
    """
    stats = parse_language_stats(html)
    expected = {"Python": 50.0, "JavaScript": 50.0}
    validate_language_stats(stats, expected)
    assert sum(stats.values()) == 100.0, "Percentages should sum to 100%"

def test_parse_language_stats_no_languages():
    """Test language stats with no language elements."""
    html = """
    <html>
        <body>
            <ul>
                <li>No language info here</li>
            </ul>
        </body>
    </html>
    """
    stats = parse_language_stats(html)
    expected = {}
    validate_language_stats(stats, expected)

def test_extract_search_urls_empty_html():
    """Test URL extraction with empty HTML."""
    urls = extract_search_urls("", "Repositories")
    expected = []
    validate_urls(urls, expected)

def test_extract_search_urls_no_links():
    """Test URL extraction with HTML but no relevant links."""
    html = """
    <html>
        <body>
            <p>No links here</p>
            <a href="/features/something">Feature link</a>
        </body>
    </html>
    """
    urls = extract_search_urls(html, "Repositories")
    expected = []
    validate_urls(urls, expected)

def test_parse_language_stats_edge_cases():
    """Test language stats with various edge cases."""
    html_negative = """
    <html><body><ul>
        <li><span class="color-fg-default text-bold mr-1">Python</span><span>-10.0%</span></li>
    </ul></body></html>
    """
    stats_negative = parse_language_stats(html_negative)
    assert len(stats_negative) == 0, "Negative percentages should be ignored"

    html_zero = """
    <html><body><ul>
        <li><span class="color-fg-default text-bold mr-1">Python</span><span>0.0%</span></li>
    </ul></body></html>
    """
    stats_zero = parse_language_stats(html_zero)
    expected_zero = {"Python": 0.0}
    validate_language_stats(stats_zero, expected_zero) 
