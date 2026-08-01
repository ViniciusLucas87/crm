import re
from datetime import UTC, datetime

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.domain.companies.entities import (
    CompanyCreate,
    CompanyListResponse,
    CompanyRead,
    CompanyUpdate,
)
from app.infrastructure.db.models import Company


class SqlAlchemyCompanyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, payload: CompanyCreate, organization_id: int) -> CompanyRead:
        company = Company(**payload.model_dump(), organization_id=organization_id)
        self._session.add(company)
        self._session.commit()
        self._session.refresh(company)
        return CompanyRead.model_validate(company)

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
    ) -> CompanyListResponse:
        filters = [Company.organization_id == organization_id]
        if not include_archived:
            filters.append(Company.is_archived.is_(False))
        if search:
            query = f"%{search.strip()}%"
            filters.append(
                or_(
                    Company.name.ilike(query),
                    Company.email.ilike(query),
                    Company.website.ilike(query),
                )
            )
        if owner:
            filters.append(Company.owner == owner)
        if status:
            filters.append(Company.status == status)

        base_query = select(Company).where(*filters)
        count_query = select(func.count()).select_from(Company).where(*filters)

        sort_columns: dict[str, object] = {
            "name": Company.name,
            "created_at": Company.created_at,
            "updated_at": Company.updated_at,
            "employees": Company.employees,
            "revenue": Company.revenue,
        }
        sort_column = sort_columns.get(sort_by, Company.created_at)
        ordering = asc(sort_column) if sort_dir == "asc" else desc(sort_column)

        rows = self._session.execute(
            base_query.order_by(ordering).offset((page - 1) * page_size).limit(page_size)
        ).scalars()
        total = self._session.execute(count_query).scalar_one()

        return CompanyListResponse(
            items=[CompanyRead.model_validate(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _get_company(self, company_id: int, organization_id: int) -> Company | None:
        return (
            self._session.execute(
                select(Company).where(
                    Company.id == company_id, Company.organization_id == organization_id
                )
            )
            .scalars()
            .first()
        )

    def get(self, company_id: int, organization_id: int) -> CompanyRead | None:
        row = self._get_company(company_id, organization_id)
        if row is None:
            return None
        return CompanyRead.model_validate(row)

    def update(self, company_id: int, payload: CompanyUpdate, organization_id: int) -> CompanyRead | None:
        row = self._get_company(company_id, organization_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        row.updated_at = datetime.now(UTC)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return CompanyRead.model_validate(row)

    def archive(self, company_id: int, organization_id: int) -> CompanyRead | None:
        row = self._get_company(company_id, organization_id)
        if row is None:
            return None
        row.is_archived = True
        row.status = "archived"
        row.updated_at = datetime.now(UTC)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return CompanyRead.model_validate(row)

    def restore(self, company_id: int, organization_id: int) -> CompanyRead | None:
        row = self._get_company(company_id, organization_id)
        if row is None:
            return None
        row.is_archived = False
        row.status = "active"
        row.updated_at = datetime.now(UTC)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return CompanyRead.model_validate(row)

    def duplicate(self, company_id: int, organization_id: int) -> CompanyRead | None:
        row = self._get_company(company_id, organization_id)
        if row is None:
            return None
        match = re.search(r"\(Copy(?: (\d+))?\)$", row.name)
        base_name = row.name[: match.start()].rstrip() if match else row.name

        existing_names = set(
            self._session.execute(
                select(Company.name).where(
                    Company.organization_id == organization_id,
                    Company.name.like(f"{base_name}%"),
                )
            ).scalars()
        )
        copy_name = f"{base_name} (Copy)"
        suffix = 2
        while copy_name in existing_names:
            copy_name = f"{base_name} (Copy {suffix})"
            suffix += 1

        duplicate_payload = CompanyCreate(
            **{
                **CompanyRead.model_validate(row).model_dump(
                    exclude={"id", "is_archived", "created_at", "updated_at"}
                ),
                "name": copy_name,
            }
        )
        return self.create(duplicate_payload, organization_id)
