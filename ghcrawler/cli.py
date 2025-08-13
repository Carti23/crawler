import argparse
import json

from .crawler import SUPPORTED_TYPES, CrawlerConfig, GitHubCrawler


def main(argv=None):
    p = argparse.ArgumentParser(description="GitHub HTML crawler (first page).")
    p.add_argument("--keywords", nargs="+", required=True, help="Search keywords")
    p.add_argument("--proxies", nargs="*", help="Proxies: host:port or scheme://host:port (optional)")
    p.add_argument("--type", choices=sorted(SUPPORTED_TYPES), required=True, help="Repositories | Issues | Wikis")
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("--extra", action="store_true", help="Include owner + language_stats (Repositories only)")
    args = p.parse_args(argv)

    cfg = CrawlerConfig(
        keywords=args.keywords,
        proxies=args.proxies,
        type=args.type,
        timeout=args.timeout,
        include_extra=args.extra,
    )
    data = GitHubCrawler(cfg).run()
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
