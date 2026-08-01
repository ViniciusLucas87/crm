from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    tasks_today: int = Field(ge=0)
    companies: int = Field(ge=0)
    active_opportunities: int = Field(ge=0)
    meetings: int = Field(ge=0)
    pipeline_value: int = Field(ge=0)
    won_deals: int = Field(ge=0)
    revenue_forecast: int = Field(ge=0)
    activities_due_today: int = Field(ge=0)
