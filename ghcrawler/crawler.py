from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import requests

from .parsers import extract_search_urls, parse_language_stats

SUPPORTED_TYPES = {"Repositories", "Issues", "Wikis"}


@dataclass
class CrawlerConfig:
    keywords: List[str]
    proxies: List[str] | None
    type: str
    timeout: int = 20
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
    include_extra: bool = False


class GitHubCrawler:
    def __init__(
        self,
        config: CrawlerConfig,
        search_parser=extract_search_urls,
        repo_lang_parser=parse_language_stats,
    ):
        if config.type not in SUPPORTED_TYPES:
            raise ValueError(f"Unsupported search type: {config.type}. "
                             f"Supported: {', '.join(sorted(SUPPORTED_TYPES))}")
        if not config.keywords:
            raise ValueError("At least one keyword is required.")

        self.config = config
        self._search_parser = search_parser
        self._repo_lang_parser = repo_lang_parser

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})

        self.proxies: Optional[Dict[str, str]] = None
        if self.config.proxies:
            chosen = random.choice(self.config.proxies)
            if "://" not in chosen:
                chosen = "http://" + chosen
            self.proxies = {"http": chosen, "https": chosen}

    def run(self) -> List[Dict[str, object]]:
        html = self._fetch(self._build_search_url())
        urls = self._search_parser(html, self.config.type)
        results: List[Dict[str, object]] = [{"url": u} for u in urls]

        if self.config.type == "Repositories" and self.config.include_extra:
            enriched: List[Dict[str, object]] = []
            for item in results:
                owner, repo = self._split_owner_repo(item["url"])
                repo_html = self._fetch(f"https://github.com/{owner}/{repo}")
                extra = {
                    "owner": owner,
                    "language_stats": self._repo_lang_parser(repo_html),
                }
                enriched.append({"url": item["url"], "extra": extra})
            return enriched

        return results

    def _build_search_url(self) -> str:
        q = quote_plus(" ".join(self.config.keywords))
        return f"https://github.com/search?q={q}&type={quote_plus(self.config.type)}"

    def _fetch(self, url: str) -> str:
        try:
            r = self.session.get(url, proxies=self.proxies, timeout=self.config.timeout)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP error fetching {url}: {e}") from e

    @staticmethod
    def _split_owner_repo(url: str) -> Tuple[str, str]:
        path = url.replace("https://github.com/", "", 1).strip("/")
        owner, repo = path.split("/", 1)
        return owner, repo
