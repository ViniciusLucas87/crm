from app.application.sales.ai_knowledge import KnowledgeBaseArchitecture


def test_pns_playbook_is_populated_and_ready_for_ai():
    knowledge = KnowledgeBaseArchitecture()
    overview = knowledge.get_overview()
    items = knowledge.get_playbook()

    assert overview.ready_for_ai is True
    assert overview.total_items == len(items)
    assert len(items) >= 12
    assert {item["category"] for item in items} >= {
        "company", "services", "sales_process", "scripts",
        "discovery", "objections", "pricing", "technical",
    }
    assert any(item["title"] == "First cold email" for item in items)
    assert all(category.status == "populated" for category in overview.categories)
