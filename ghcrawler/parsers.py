from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup, FeatureNotFound

from .selectors import LANGUAGE_NAME_SELECTOR, PERCENT_RE, RESERVED_NAMESPACES

GITHUB_BASE_URL = "https://github.com"


def _soup(html: str) -> BeautifulSoup:
    """Create a BeautifulSoup using fast parser if available (lxml -> html.parser fallback)."""
    try:
        return BeautifulSoup(html, "lxml")
    except (FeatureNotFound, Exception):
        return BeautifulSoup(html, "html.parser")


def _abs_github_url(href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return urljoin(GITHUB_BASE_URL, href)


def _is_repo_path(path: str) -> bool:
    """True for '/owner/repo' path (no deeper segment)."""
    if not path.startswith("/"):
        return False
    segs = [s for s in path.split("/") if s]
    if len(segs) != 2:
        return False
    owner, repo = segs
    if owner in RESERVED_NAMESPACES:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+", owner)) and bool(re.fullmatch(r"[A-Za-z0-9_.-]+", repo))


def extract_search_urls(html: str, search_type: str) -> List[str]:
    """Extract result URLs from a GitHub search page for the given type.

    - Repositories: '/{owner}/{repo}'
    - Issues: '/{owner}/{repo}/issues/{number}'
    - Wikis: '/{owner}/{repo}/wiki'
    """
    soup = _soup(html)
    urls: List[str] = []

    if search_type == "Repositories":
        for a in soup.select("a.v-align-middle"):
            href = a.get("href") or ""
            if _is_repo_path(href):
                urls.append(_abs_github_url(href))

        if not urls:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if _is_repo_path(href):
                    urls.append(_abs_github_url(href))

    elif search_type == "Issues":
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"^/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/\d+$", href):
                urls.append(_abs_github_url(href))

    elif search_type == "Wikis":
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r"^/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/wiki$", href):
                urls.append(_abs_github_url(href))

    seen = set()
    unique_urls: List[str] = []
    for u in urls:
        if u not in seen:
            unique_urls.append(u)
            seen.add(u)
    return unique_urls


def parse_language_stats(html: str) -> Dict[str, float]:
    """Parse language stats from a GitHub repository page.

    Supports two forms:
    1) The modern markup with LANGUAGE_NAME_SELECTOR for names + sibling span with percent.
    2) Fallback to any list item containing a percent like '73.4%' and a plausible language name.
    """
    soup = _soup(html)
    results: Dict[str, float] = {}

    for li in soup.find_all("li"):
        name_el = li.select_one(LANGUAGE_NAME_SELECTOR)
        if not name_el:
            continue

        percent_text = None
        for span in li.find_all("span"):
            txt = span.get_text(strip=True)
            if re.fullmatch(PERCENT_RE, txt or ""):
                percent_text = txt
                break

        if percent_text is None:
            m = re.search(PERCENT_RE, li.get_text(" ", strip=True))
            if not m:
                continue
            percent_text = m.group(1) + "%"

        language_name = name_el.get_text(strip=True)
        m2 = re.search(PERCENT_RE, percent_text)
        if not m2:
            continue
        try:
            value = float(m2.group(1))
        except ValueError:
            continue

        if language_name:
            results[language_name] = value

    return results
