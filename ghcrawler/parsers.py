from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .selectors import LANGUAGE_NAME_SELECTOR, PERCENT_RE, RESERVED_NAMESPACES

GITHUB_BASE_URL = "https://github.com"


def _extract_github_links(soup: BeautifulSoup) -> List[str]:
    """Return absolute https://github.com/... links from all <a href> in the soup."""
    links: List[str] = []
    
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.startswith("//"):
            continue

        if href.startswith("/"):
            absolute_url = urljoin(GITHUB_BASE_URL + "/", href)
        else:
            absolute_url = href

        if absolute_url.startswith(GITHUB_BASE_URL + "/"):
            clean_url = absolute_url.split("#", 1)[0].split("?", 1)[0]
            links.append(clean_url)
    
    return links


def extract_search_urls(html: str, search_type: str) -> List[str]:
    """Extract normalized GitHub URLs for a given search type from the first page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    seen_urls: set[str] = set()
    result_urls: List[str] = []

    def add_unique_url(url: str) -> None:
        if url not in seen_urls:
            seen_urls.add(url)
            result_urls.append(url)

    hrefs = _extract_github_links(soup)

    if search_type == "Repositories":
        for href in hrefs:
            path = href.removeprefix(GITHUB_BASE_URL + "/")
            parts = [part for part in path.split("/") if part]
            
            if (len(parts) == 2 and 
                parts[0] not in RESERVED_NAMESPACES and 
                parts[1] not in RESERVED_NAMESPACES):
                add_unique_url(f"{GITHUB_BASE_URL}/{parts[0]}/{parts[1]}")

    elif search_type == "Issues":
        for href in hrefs:
            path = href.removeprefix(GITHUB_BASE_URL + "/")
            parts = [part for part in path.split("/") if part]
            
            if (len(parts) >= 4 and 
                parts[2] == "issues" and 
                parts[0] not in RESERVED_NAMESPACES):
                add_unique_url(f"{GITHUB_BASE_URL}/{'/'.join(parts[:4])}")

    elif search_type == "Wikis":
        for href in hrefs:
            path = href.removeprefix(GITHUB_BASE_URL + "/")
            parts = [part for part in path.split("/") if part]
            
            if (len(parts) >= 4 and 
                parts[2] == "wiki" and 
                parts[0] not in RESERVED_NAMESPACES):
                add_unique_url(f"{GITHUB_BASE_URL}/{'/'.join(parts[:4])}")

    return result_urls


def parse_language_stats(html: str) -> Dict[str, float]:
    """Parse language usage from a repository page's language stats block.
    Returns a dict of {language: percentage} normalized to sum to 100 (if possible).
    """
    soup = BeautifulSoup(html, "html.parser")
    stats: Dict[str, float] = {}

    for list_item in soup.select("ul li"):
        name_element = list_item.select_one(LANGUAGE_NAME_SELECTOR)
        if not name_element:
            continue

        percentage_text = None
        for span in list_item.find_all("span"):
            if span is name_element:
                continue
            text = span.get_text(strip=True)
            if text.endswith("%"):
                percentage_text = text[:-1]
                break

        if percentage_text is None:
            match = re.search(PERCENT_RE, list_item.get_text(" ", strip=True))
            if not match:
                continue
            percentage_text = match.group(1)

        language_name = name_element.get_text(strip=True)
        try:
            percentage = float(percentage_text)
        except ValueError:
            continue

        if 0 <= percentage <= 100:
            stats[language_name] = percentage

    total = sum(stats.values())
    if total > 0:
        normalized_stats = {}
        for language, percentage in stats.items():
            normalized_stats[language] = round(percentage * 100.0 / total, 1)
        return normalized_stats

    return stats
