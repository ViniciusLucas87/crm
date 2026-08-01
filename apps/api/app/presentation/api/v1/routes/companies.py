from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.companies.services import CompanyService
from app.application.events.bridge import emit
from app.application.workers.events import EventType
from app.domain.companies.entities import (
    CompanyCreate,
    CompanyListResponse,
    CompanyRead,
    CompanyUpdate,
)
from app.infrastructure.auth.clerk import AuthContext, require_permission
from app.infrastructure.db.session import get_db_session
from app.presentation.api.v1.deps import get_company_service

router = APIRouter()


@router.post("", response_model=CompanyRead)
def create_company(
    payload: CompanyCreate,
    context: AuthContext = Depends(require_permission("companies:write")),
    service: CompanyService = Depends(get_company_service),
    session: Session = Depends(get_db_session),
) -> CompanyRead:
    result = service.create(payload, context.organization_id)
    emit(session, EventType.COMPANY_CREATED, "company", result.id, {"name": result.name})
    return result


@router.get("", response_model=CompanyListResponse)
def list_companies(
    context: AuthContext = Depends(require_permission("companies:read")),
    service: CompanyService = Depends(get_company_service),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    owner: str | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    include_archived: bool = Query(default=False),
) -> CompanyListResponse:
    return service.list(
        page=page,
        page_size=page_size,
        search=search,
        owner=owner,
        organization_id=context.organization_id,
        status_value=status_value,
        sort_by=sort_by,
        sort_dir=sort_dir,
        include_archived=include_archived,
    )


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: int,
    context: AuthContext = Depends(require_permission("companies:read")),
    service: CompanyService = Depends(get_company_service),
) -> CompanyRead:
    return service.get(company_id, context.organization_id)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    context: AuthContext = Depends(require_permission("companies:write")),
    service: CompanyService = Depends(get_company_service),
    session: Session = Depends(get_db_session),
) -> CompanyRead:
    result = service.update(company_id, payload, context.organization_id)
    emit(session, EventType.COMPANY_UPDATED, "company", company_id, {"fields": list(payload.model_dump(exclude_unset=True).keys())})
    return result


@router.delete("/{company_id}", response_model=CompanyRead)
def archive_company(
    company_id: int,
    context: AuthContext = Depends(require_permission("companies:write")),
    service: CompanyService = Depends(get_company_service),
    session: Session = Depends(get_db_session),
) -> CompanyRead:
    result = service.archive(company_id, context.organization_id)
    emit(session, EventType.COMPANY_ARCHIVED, "company", company_id)
    return result


@router.post("/{company_id}/restore", response_model=CompanyRead)
def restore_company(
    company_id: int,
    context: AuthContext = Depends(require_permission("companies:write")),
    service: CompanyService = Depends(get_company_service),
) -> CompanyRead:
    return service.restore(company_id, context.organization_id)


@router.post("/{company_id}/duplicate", response_model=CompanyRead)
def duplicate_company(
    company_id: int,
    context: AuthContext = Depends(require_permission("companies:write")),
    service: CompanyService = Depends(get_company_service),
) -> CompanyRead:
    return service.duplicate(company_id, context.organization_id)
