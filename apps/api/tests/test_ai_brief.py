from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.sales.ai_brief import DailyBriefEngine
from app.infrastructure.db.base import Base
from app.infrastructure.db.social_leads import SocialLeadCampaign, SocialLeadOpportunity


def test_daily_brief_reports_real_social_outreach_and_excludes_tests() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        campaign = SocialLeadCampaign(
            organization_id=1,
            channel="reddit",
            name="Never Miss",
            product_code="never-miss",
            audience="Canadian contractors",
            offer_summary="Missed call recovery",
            public_reply_guidance="Help first",
            dm_guidance="Ask permission",
        )
        session.add(campaign)
        session.flush()
        session.add_all([
            SocialLeadOpportunity(
                organization_id=1,
                campaign_id=campaign.id,
                channel="reddit",
                community="plumbing",
                author_handle="real_contractor",
                post_title="Missing calls on jobs",
                post_excerpt="I cannot answer every call.",
                source_url="https://reddit.example/real",
                relevance_reason="Clear missed call pain",
                status="reply_ready",
            ),
            SocialLeadOpportunity(
                organization_id=1,
                campaign_id=campaign.id,
                channel="reddit",
                community="testing",
                author_handle="pns_internal_test",
                post_title="Internal test",
                post_excerpt="Test",
                source_url="https://reddit.example/test",
                relevance_reason="Test",
                status="contacted",
                contacted_at=datetime.now(UTC),
            ),
        ])
        session.commit()

        brief = DailyBriefEngine(session, 1).generate()

    reddit = next(item for item in brief.outreach if item.channel == "reddit")
    assert reddit.total == 1
    assert reddit.ready == 1
    assert reddit.contacted == 0
    assert any("Reddit test record excluded" in item.title for item in brief.data_warnings)
    assert any("Reddit replies" in item.title for item in brief.actions)
