import importlib

from fastapi.testclient import TestClient


def _load_app(monkeypatch, environment: str):
    monkeypatch.setenv("PNS_ENV", environment)

    import app.core.config as config_module
    import app.main as main_module

    config_module.get_settings.cache_clear()
    return importlib.reload(main_module).app


def test_developer_docs_are_hidden_in_production(monkeypatch):
    client = TestClient(_load_app(monkeypatch, "production"))

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_developer_docs_remain_available_in_development(monkeypatch):
    client = TestClient(_load_app(monkeypatch, "development"))

    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200
