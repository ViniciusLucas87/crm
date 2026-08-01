from fastapi import HTTPException, status

from app.domain.companies.entities import (
    CompanyCreate,
    CompanyListResponse,
    CompanyRead,
    CompanyUpdate,
)
from app.domain.companies.repositories import CompanyRepository


class CompanyService:
    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    def create(self, payload: CompanyCreate, organization_id: int) -> CompanyRead:
        return self._repository.create(payload, organization_id)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        owner: str | None,
        organization_id: int,
        status_value: str | None,
        sort_by: str,
        sort_dir: str,
        include_archived: bool,
    ) -> CompanyListResponse:
        return self._repository.list(
            page=page,
            page_size=page_size,
            search=search,
            owner=owner,
            organization_id=organization_id,
            status=status_value,
            sort_by=sort_by,
            sort_dir=sort_dir,
            include_archived=include_archived,
        )

    def get(self, company_id: int, organization_id: int) -> CompanyRead:
        record = self._repository.get(company_id, organization_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return record

    def update(self, company_id: int, payload: CompanyUpdate, organization_id: int) -> CompanyRead:
        record = self._repository.update(company_id, payload, organization_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return record

    def archive(self, company_id: int, organization_id: int) -> CompanyRead:
        record = self._repository.archive(company_id, organization_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return record

    def restore(self, company_id: int, organization_id: int) -> CompanyRead:
        record = self._repository.restore(company_id, organization_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return record

    def duplicate(self, company_id: int, organization_id: int) -> CompanyRead:
        record = self._repository.duplicate(company_id, organization_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return record
