from typing import Protocol

from app.domain.companies.entities import (
    CompanyCreate,
    CompanyListResponse,
    CompanyRead,
    CompanyUpdate,
)


class CompanyRepository(Protocol):
    def create(self, payload: CompanyCreate, organization_id: int) -> CompanyRead: ...

    def list(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        owner: str | None,
        organization_id: int,
        status: str | None,
        sort_by: str,
        sort_dir: str,
        include_archived: bool,
    ) -> CompanyListResponse: ...

    def get(self, company_id: int, organization_id: int) -> CompanyRead | None: ...

    def update(
        self, company_id: int, payload: CompanyUpdate, organization_id: int
    ) -> CompanyRead | None: ...

    def archive(self, company_id: int, organization_id: int) -> CompanyRead | None: ...

    def restore(self, company_id: int, organization_id: int) -> CompanyRead | None: ...

    def duplicate(self, company_id: int, organization_id: int) -> CompanyRead | None: ...
