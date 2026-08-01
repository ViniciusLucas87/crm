"""
Intelligence Provider — abstract interface.

Every intelligence source (Google Maps, LinkedIn, Website Crawling, etc.)
implements this interface and plugs into the Intelligence Pipeline.

ADR: docs/adr-001-intelligence-pipeline.md §10
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntelligenceResult:
    """Normalized output from any Intelligence Provider.

    Every provider returns this structure. The pipeline stores it as JSON
    with provenance tracking baked in.
    """

    provider_name: str
    stage_name: str
    status: str = "completed"  # completed | failed | partial
    data: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    processing_time_ms: int = 0

    def to_json(self) -> str:
        import json

        return json.dumps(
            {
                "provider": self.provider_name,
                "stage": self.stage_name,
                "status": self.status,
                "data": self.data,
                "provenance": self.provenance,
                "errors": self.errors,
                "processing_time_ms": self.processing_time_ms,
            }
        )


class IntelligenceProvider(ABC):
    """Abstract interface for all Intelligence Providers.

    Usage:
        class GoogleMapsProvider(IntelligenceProvider):
            @property
            def provider_name(self) -> str: return "google_maps"
            @property
            def stage_name(self) -> str: return "Google Maps Intelligence"

            async def collect(self, company: dict) -> dict: ...
            def normalize(self, raw: dict) -> dict: ...
            def validate(self, data: dict) -> list[str]: ...
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier: 'google_maps', 'linkedin', 'website', etc."""
        ...

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Human-readable: 'Google Maps Intelligence', 'LinkedIn Intelligence', etc."""
        ...

    @abstractmethod
    async def collect(self, company: dict[str, Any]) -> dict[str, Any]:
        """Gather raw data from the external source.

        Args:
            company: Dict with keys: name, website, city, province, industry, employees, etc.

        Returns:
            Raw provider-specific data dict.
        """
        ...

    @abstractmethod
    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Transform raw provider data into a provider-independent schema.

        The normalized schema should be consistent across providers so
        the rest of the application never depends on raw API responses.
        """
        ...

    def validate(self, data: dict[str, Any]) -> list[str]:
        """Validate normalized data. Return list of error messages (empty = valid)."""
        return []

    async def execute(self, company: dict[str, Any]) -> IntelligenceResult:
        """Full execution: collect → normalize → validate → result.

        This is the single entry point called by Celery tasks.
        Subclasses should NOT override this — override collect/normalize instead.
        """
        import time

        start = time.time()
        errors: list[str] = []

        try:
            raw = await self.collect(company)
        except Exception as e:
            return IntelligenceResult(
                provider_name=self.provider_name,
                stage_name=self.stage_name,
                status="failed",
                errors=[f"Collection failed: {e}"],
                processing_time_ms=int((time.time() - start) * 1000),
            )

        try:
            normalized = self.normalize(raw)
        except Exception as e:
            return IntelligenceResult(
                provider_name=self.provider_name,
                stage_name=self.stage_name,
                status="failed",
                errors=[f"Normalization failed: {e}"],
                processing_time_ms=int((time.time() - start) * 1000),
            )

        validation_errors = self.validate(normalized)
        if validation_errors:
            errors.extend(validation_errors)

        # Build provenance — every field tagged with its source
        provenance = {
            key: f"{self.provider_name} ({self.stage_name})"
            for key in normalized
        }

        return IntelligenceResult(
            provider_name=self.provider_name,
            stage_name=self.stage_name,
            status="completed" if not errors else "partial",
            data=normalized,
            provenance=provenance,
            errors=errors,
            processing_time_ms=int((time.time() - start) * 1000),
        )
