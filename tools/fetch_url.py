"""HTTP fetching and same-domain crawling helpers (fetch_html, crawl_website, link resolution) shared by the website and Instagram agents."""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlsplit, urldefrag
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    )
}


def fetch_html(url: str, timeout: int = 15) -> str:
    logger.info(f"[fetch_url] GET {url} (timeout={timeout}s)")
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
        logger.info(f"[fetch_url] OK {url} status={resp.status_code} len={len(resp.text)}")
        return resp.text
    except Exception as e:
        logger.warning(f"[fetch_url] ERROR {url}: {e}")
        return f"""<!-- FETCH_ERROR: {e} -->"""


def absolute_url(base_url: str, href: str) -> str:
    return urldefrag(urljoin(base_url, href))[0]


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text(" \n ")
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        href_abs = absolute_url(base_url, href)
        links.append(href_abs)
    return links


def crawl_website(root_url: str, max_pages: int = 5) -> Tuple[str, List[str]]:
    """
    Crawl a site up to ~1 depth, aggregate text content.
    Returns (combined_text, visited_urls)
    """
    if max_pages < 1:
        return "", []
    root_url = urldefrag(root_url)[0]
    visited: List[str] = []
    combined_text_parts: List[str] = []

    logger.info(f"[crawl] root={root_url} max_pages={max_pages}")
    root_html = fetch_html(root_url)
    visited.append(root_url)
    combined_text_parts.append(extract_visible_text(root_html))
    links = extract_links(root_html, root_url)

    root_origin = urlsplit(root_url)

    for link in links:
        if len(visited) >= max_pages:
            break
        origin = urlsplit(link)
        if (origin.scheme, origin.netloc) != (root_origin.scheme, root_origin.netloc):
            continue
        if link in visited:
            continue
        logger.info(f"[crawl] visiting {link}")
        html = fetch_html(link)
        visited.append(link)
        combined_text_parts.append(extract_visible_text(html))

    combined_text = "\n\n".join([p for p in combined_text_parts if p])
    logger.info(f"[crawl] visited={len(visited)} pages")
    return combined_text, visited
