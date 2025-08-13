from unittest.mock import Mock, patch

import pytest

from ghcrawler.crawler import CrawlerConfig, GitHubCrawler


def mk(**over):
    base = dict(keywords=["python","django-rest-framework","jwt"], proxies=["1.2.3.4:8080"], type="Repositories", timeout=5)
    base.update(over); return CrawlerConfig(**base)

@patch("requests.Session.get")
def test_filters_out_topics_and_features(mock_get):
    html = """
    <html><body>
      <a href="/features/copilot">feat</a>
      <a href="/topics/python">topic</a>
      <a href="/user1/repo1">ok</a>
      <a href="/search/advanced">search</a>
    </body></html>
    """
    resp = Mock(); resp.raise_for_status = Mock(); resp.text = html; mock_get.return_value = resp
    urls = [x["url"] for x in GitHubCrawler(mk()).run()]
    assert "https://github.com/user1/repo1" in urls
    assert not any("/features/" in u or "/topics/" in u or "/search/" in u for u in urls)

@patch("requests.Session.get")
def test_extra_enrichment_languages(mock_get):
    search_html = "<html><body><a href='/ownerX/repoY'>r</a></body></html>"
    repo_html = """
    <html><body>
        <ul>
            <li>
                <span class="color-fg-default text-bold mr-1">Python</span>
                <span>100.0%</span>
            </li>
        </ul>
    </body></html>
    """

    def side_effect(url, **kwargs):
        m = Mock(); m.raise_for_status = Mock()
        m.text = repo_html if url.endswith("/ownerX/repoY") else search_html
        return m

    mock_get.side_effect = side_effect

    out = GitHubCrawler(mk()).run()  # no extras
    assert "extra" not in out[0]

    out2 = GitHubCrawler(mk(include_extra=True)).run()
    assert out2[0]["extra"]["owner"] == "ownerX"
    langs = out2[0]["extra"]["language_stats"]
    assert langs and isinstance(langs, dict) and langs.get("Python") == 100.0

def test_invalid_search_type():
    """Test error handling for invalid search type (line 34)"""
    with pytest.raises(ValueError, match="Unsupported search type"):
        GitHubCrawler(mk(type="InvalidType"))

def test_empty_keywords():
    """Test error handling for empty keywords (line 37)"""
    with pytest.raises(ValueError, match="At least one keyword is required"):
        GitHubCrawler(mk(keywords=[]))

def test_crawler_config_defaults():
    """Test CrawlerConfig default values"""
    config = CrawlerConfig(
        keywords=["test"],
        proxies=None,
        type="Repositories"
    )
    assert config.timeout == 20
    assert config.include_extra is False
    assert "Chrome" in config.user_agent

def test_crawler_config_custom_values():
    """Test CrawlerConfig with custom values"""
    config = CrawlerConfig(
        keywords=["test"],
        proxies=["1.2.3.4:8080"],
        type="Repositories",
        timeout=30,
        include_extra=True
    )
    assert config.timeout == 30
    assert config.include_extra is True
    assert config.proxies == ["1.2.3.4:8080"]
