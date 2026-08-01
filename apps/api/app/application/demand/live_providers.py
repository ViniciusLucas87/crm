import asyncio
import json
import re
from typing import Any

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.application.demand.provider import RawSignal, SignalProvider, SignalSource
from app.infrastructure.db.models import Company, Lead


class RedditSignalProvider(SignalProvider):
    @property
    def provider_name(self) -> str:
        return SignalSource.REDDIT.value

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[RawSignal]:
        headers = {"User-Agent": "PNS-TITAN/1.0"}
        url = "https://www.reddit.com/search.json"
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
                response = await client.get(url, params={"q": query, "limit": 5, "sort": "new"})
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return []

        items = payload.get("data", {}).get("children", [])
        results: list[RawSignal] = []
        for item in items:
            data = item.get("data", {})
            title = data.get("title") or ""
            body = data.get("selftext") or title
            permalink = data.get("permalink") or ""
            if not title:
                continue
            results.append(
                RawSignal(
                    source=SignalSource.REDDIT,
                    source_url=f"https://www.reddit.com{permalink}",
                    title=title,
                    content=body[:4000],
                    author=data.get("author"),
                    company_name=_extract_company_name(title, body),
                    published_at=None,
                    location=None,
                    metadata={"subreddit": data.get("subreddit")},
                )
            )
        return results

    async def normalize(self, raw: RawSignal):
        raise NotImplementedError()


class CompanyWebsiteSignalProvider(SignalProvider):
    def __init__(self, db: Session):
        self._db = db

    @property
    def provider_name(self) -> str:
        return SignalSource.COMPANY_WEBSITE.value

    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[RawSignal]:
        companies = self._db.execute(
            select(Company.id, Company.name, Company.website, Company.description, Company.buying_signals).where(
                Company.is_archived.is_(False),
                or_(Company.name.ilike(f"%{query}%"), Company.description.ilike(f"%{query}%"), Company.buying_signals.ilike(f"%{query}%")),
            ).limit(10)
        ).all()
        leads = self._db.execute(
            select(Lead.id, Lead.name, Lead.website, Lead.description).where(
                or_(Lead.name.ilike(f"%{query}%"), Lead.description.ilike(f"%{query}%"))
            ).limit(10)
        ).all()

        urls = []
        for row in companies:
            if row.website:
                urls.append((row.name, row.website, row.description or "", row.buying_signals or ""))
        for row in leads:
            if row.website:
                urls.append((row.name, row.website, row.description or "", ""))

        results: list[RawSignal] = []
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            for company_name, website, description, buying_signals in urls[:6]:
                content_parts = [description, buying_signals]
                try:
                    homepage = await client.get(website if website.startswith("http") else f"https://{website}")
                    if homepage.status_code < 400:
                        text = _strip_html(homepage.text)
                        content_parts.append(text[:2500])
                    try:
                        careers = await client.get((website if website.startswith("http") else f"https://{website}").rstrip("/") + "/careers")
                        if careers.status_code < 400:
                            content_parts.append(_strip_html(careers.text)[:1500])
                    except Exception:
                        pass
                except Exception:
                    pass

                content = "\n".join(part for part in content_parts if part)
                if not content:
                    continue
                results.append(
                    RawSignal(
                        source=SignalSource.COMPANY_WEBSITE,
                        source_url=website,
                        title=f"{company_name} website signal",
                        content=content[:4000],
                        company_name=company_name,
                        metadata={"provider": "company_website"},
                    )
                )
        return results

    async def normalize(self, raw: RawSignal):
        raise NotImplementedError()


class ProviderRegistry:
    def __init__(self, db: Session):
        self._providers: dict[str, SignalProvider] = {
            SignalSource.REDDIT.value: RedditSignalProvider(),
            SignalSource.COMPANY_WEBSITE.value: CompanyWebsiteSignalProvider(db),
        }

    async def search(self, query: str, sources: list[str] | None = None, filters: dict[str, Any] | None = None) -> list[RawSignal]:
        selected = self._providers
        if sources:
            selected = {k: v for k, v in self._providers.items() if k in sources}
        batches = await asyncio.gather(*(provider.search(query, filters) for provider in selected.values()), return_exceptions=True)
        results: list[RawSignal] = []
        for batch in batches:
            if isinstance(batch, Exception):
                continue
            results.extend(batch)
        return results


def _strip_html(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_company_name(title: str, body: str) -> str | None:
    text = f"{title} {body}"
    match = re.search(r"([A-Z][A-Za-z0-9&'\-. ]{2,40})(?:\s+(?:Inc|Ltd|LLC|Corp|Company|Services))?", text)
    return match.group(1).strip() if match else None