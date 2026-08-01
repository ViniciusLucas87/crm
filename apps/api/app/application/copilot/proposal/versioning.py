"""
Proposal Versioning — track, compare, and manage proposal versions.

Supports version history, diff comparison, and rollback.
"""

from __future__ import annotations

from datetime import datetime, UTC

from app.application.copilot.proposal.models import Proposal, ProposalVersion, ProposalSection


class ProposalVersionManager:
    """Manages proposal versioning with history and comparison."""

    def create_version(
        self, proposal: Proposal, generated_by: str = "system", reason: str = "Initial generation"
    ) -> ProposalVersion:
        now = datetime.now(UTC).isoformat()
        version_num = len(proposal.versions) + 1

        version = ProposalVersion(
            version=version_num,
            created_at=now,
            generated_by=generated_by,
            reason=reason,
            sections=[
                ProposalSection(
                    id=s.id, title=s.title, content=s.content,
                    status=s.status, generated_at=s.generated_at,
                    metadata=s.metadata,
                )
                for s in proposal.sections
            ],
        )
        proposal.versions.append(version)
        proposal.current_version = version_num
        return version

    def compare(self, v1: ProposalVersion, v2: ProposalVersion) -> dict:
        """Compare two versions and return changes."""
        changes: dict[str, dict] = {}

        v1_sections = {s.id: s for s in v1.sections}
        v2_sections = {s.id: s for s in v2.sections}

        # Added sections
        for sid in v2_sections:
            if sid not in v1_sections:
                changes[sid] = {"type": "added", "title": v2_sections[sid].title}

        # Removed sections
        for sid in v1_sections:
            if sid not in v2_sections:
                changes[sid] = {"type": "removed", "title": v1_sections[sid].title}

        # Modified sections
        for sid in set(v1_sections) & set(v2_sections):
            if v1_sections[sid].content != v2_sections[sid].content:
                changes[sid] = {"type": "modified", "title": v2_sections[sid].title}

        return changes

    def rollback(self, proposal: Proposal, version_num: int) -> Proposal | None:
        """Roll back to a previous version."""
        for v in proposal.versions:
            if v.version == version_num:
                proposal.sections = [
                    ProposalSection(
                        id=s.id, title=s.title, content=s.content,
                        status=s.status, generated_at=s.generated_at,
                        metadata=s.metadata,
                    )
                    for s in v.sections
                ]
                proposal.current_version = version_num
                return proposal
        return None


# Singleton
_manager: ProposalVersionManager | None = None


def get_version_manager() -> ProposalVersionManager:
    global _manager
    if _manager is None:
        _manager = ProposalVersionManager()
    return _manager
