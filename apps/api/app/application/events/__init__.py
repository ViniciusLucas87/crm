"""Event Bridge — connects CRUD operations to the Worker Event Bus."""
from app.application.events.bridge import emit

__all__ = ["emit"]
