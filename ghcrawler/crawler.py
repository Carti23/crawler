from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .parsers import extract_search_urls, parse_language_stats

SUPPORTED_TYPES = {"Repositories", "Issues", "Wikis"}


@dataclass
class CrawlerConfig:
    keywords: List[str]
    proxies: Optional[List[str]]
    type: str
    timeout: int = 20
    include_extra: bool = False
    concurrency: int = 16
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0 Safari/537.36"
    )


class GitHubCrawler:
    def __init__(self, config: CrawlerConfig):
        if config.type not in SUPPORTED_TYPES:
            raise ValueError(f"Unsupported search type: {config.type}")
        if not config.keywords:
            raise ValueError("At least one keyword is required")
        self.config = config
        self.session = self._build_session(config)
        self.proxies = config.proxies or []

    def _build_session(self, cfg: CrawlerConfig) -> requests.Session:
        s = requests.Session()
        s.headers.update({"User-Agent": cfg.user_agent, "Accept-Language": "en-US,en;q=0.9"})
        # Pool size ~ concurrency, with retries/backoff for transient GitHub responses
        pool = max(4, int(cfg.concurrency))
        adapter = HTTPAdapter(
            pool_connections=pool,
            pool_maxsize=pool,
            max_retries=Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset(["GET", "HEAD"]),
                raise_on_status=False,
            ),
        )
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        return s

    def _choose_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        if "://" not in proxy:
            proxy = f"http://{proxy}"
        return {"http": proxy, "https": proxy}

    def _fetch(self, url: str) -> str:
        try:
            r = self.session.get(url, proxies=self._choose_proxy(), timeout=self.config.timeout)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP error fetching {url}: {e}") from e

    def run(self) -> List[Dict]:
        search_url = self._build_search_url()
        html = self._fetch(search_url)
        urls = extract_search_urls(html, self.config.type)
        results: List[Dict] = [{"url": u} for u in urls]

        if self.config.type == "Repositories" and self.config.include_extra and results:
            concurrency = max(1, int(self.config.concurrency))
            enriched: List[Optional[Dict]] = [None] * len(results)

            def task(index_url: Tuple[int, str]) -> Tuple[int, Dict]:
                idx, repo_url = index_url
                owner, repo = self._split_owner_repo(repo_url)
                repo_html = self._fetch(f"https://github.com/{owner}/{repo}")
                langs = parse_language_stats(repo_html)
                item = {
                    "url": repo_url,
                    "extra": {"owner": owner, "repo": repo, "language_stats": langs},
                }
                return idx, item

            with ThreadPoolExecutor(max_workers=concurrency) as tp:
                future_to_idx = {tp.submit(task, (i, item["url"])): i for i, item in enumerate(results)}
                for fut in as_completed(future_to_idx):
                    idx, enriched_item = fut.result()
                    enriched[idx] = enriched_item

            return [item for item in enriched if item is not None]

        return results

    def _build_search_url(self) -> str:
        q = quote_plus(" ".join(self.config.keywords))
        t = quote_plus(self.config.type)
        return f"https://github.com/search?q={q}&type={t}"

    @staticmethod
    def _split_owner_repo(url: str) -> Tuple[str, str]:
        if url.startswith("https://github.com/"):
            path = url[len("https://github.com/"):]
        else:
            path = url.lstrip("/")
        owner, repo = path.split("/", 1)
        return owner, repo
