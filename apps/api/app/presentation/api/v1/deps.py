from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.companies.services import CompanyService
from app.application.dashboard.services import DashboardService
from app.application.sales.services import ActivityService, ContactService, OpportunityService, TaskService
from app.application.sales.timeline_service import TimelineService
from app.infrastructure.db.session import get_db_session
from app.infrastructure.repositories.company_repository import SqlAlchemyCompanyRepository
from app.infrastructure.repositories.dashboard_repository import SqlDashboardRepository
from app.infrastructure.repositories.sales_repository import SqlActivityRepository, SqlContactRepository, SqlOpportunityRepository, SqlTaskRepository
from app.infrastructure.repositories.timeline_repository import SqlTimelineRepository


def get_dashboard_service(session: Session = Depends(get_db_session)) -> DashboardService:
    repository = SqlDashboardRepository(session=session)
    return DashboardService(repository=repository)


def get_company_service(session: Session = Depends(get_db_session)) -> CompanyService:
    repository = SqlAlchemyCompanyRepository(session=session)
    return CompanyService(repository=repository)


def get_contact_service(session: Session = Depends(get_db_session)) -> ContactService:
    return ContactService(SqlContactRepository(session=session))


def get_activity_service(session: Session = Depends(get_db_session)) -> ActivityService:
    return ActivityService(SqlActivityRepository(session=session))


def get_task_service(session: Session = Depends(get_db_session)) -> TaskService:
    return TaskService(SqlTaskRepository(session=session))


def get_opportunity_service(session: Session = Depends(get_db_session)) -> OpportunityService:
    return OpportunityService(SqlOpportunityRepository(session=session))


def get_timeline_service(session: Session = Depends(get_db_session)) -> TimelineService:
    return TimelineService(SqlTimelineRepository(session=session))
