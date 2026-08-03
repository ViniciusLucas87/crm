"""Safe, bounded public-website evidence collection for lead research."""

from __future__ import annotations

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx


MAX_RESPONSE_BYTES = 1_000_000
MAX_TEXT_CHARS = 12_000


class _EvidenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self._in_title = False
        self._skip_depth = 0
        self.text: list[str] = []
        self.emails: set[str] = set()
        self.phones: set[str] = set()
        self.links: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag in {"script", "style", "svg", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and values.get("name", "").lower() in {"description", "og:description"}:
            self.description = values.get("content", "").strip()
        if tag == "a":
            href = values.get("href", "").strip()
            if href.startswith("mailto:"):
                self.emails.add(href[7:].split("?", 1)[0])
            elif href.startswith("tel:"):
                self.phones.add(href[4:].strip())
            elif href:
                lowered = href.lower()
                for key in ("contact", "about", "team", "leadership", "services", "careers"):
                    if key in lowered and key not in self.links:
                        self.links[key] = href

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if not value:
            return
        if self._in_title:
            self.title = f"{self.title} {value}".strip()
        elif not self._skip_depth:
            self.text.append(value)


def _validate_public_url(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("No website provided")
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Website must be a public HTTP(S) URL")
    if parsed.username or parsed.password:
        raise ValueError("Website credentials are not allowed")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except socket.gaierror as exc:
        raise ValueError("Website hostname could not be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError("Private or local website addresses are not allowed")
    return candidate


async def collect_website_evidence(website: str) -> dict[str, object]:
    """Fetch one public page and return bounded, attributable business evidence."""
    url = _validate_public_url(website)
    headers = {"User-Agent": "PacificNorthSystemsResearch/1.0 (+https://pacificnorthsystems.com)"}
    async with httpx.AsyncClient(headers=headers, timeout=12.0, follow_redirects=False) as client:
        response = None
        current_url = url
        for _ in range(5):
            current_url = _validate_public_url(current_url)
            response = await client.get(current_url)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise ValueError("Website returned an invalid redirect")
                current_url = urljoin(current_url, location)
                continue
            break
        if response is None or response.is_redirect:
            raise ValueError("Website redirected too many times")
        response.raise_for_status()
        final_url = _validate_public_url(str(response.url))
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            raise ValueError("Website did not return HTML")
        raw = response.content[:MAX_RESPONSE_BYTES]

    parser = _EvidenceParser()
    parser.feed(raw.decode(response.encoding or "utf-8", errors="replace"))
    text = " ".join(parser.text)
    text = re.sub(r"\s+", " ", text)[:MAX_TEXT_CHARS]
    requested_host = (urlparse(url).hostname or "").removeprefix("www.")
    final_host = (urlparse(final_url).hostname or "").removeprefix("www.")
    return {
        "requested_url": url,
        "source_url": final_url,
        "redirected_cross_domain": requested_host != final_host,
        "title": parser.title[:300],
        "meta_description": parser.description[:1_000],
        "emails": sorted(filter(None, parser.emails))[:10],
        "phones": sorted(filter(None, parser.phones))[:10],
        "important_links": {key: urljoin(final_url, href) for key, href in parser.links.items()},
        "page_text": text,
        "evidence_chars": len(text),
    }
