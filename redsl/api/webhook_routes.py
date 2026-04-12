"""GitHub webhook endpoints."""

from __future__ import annotations

from typing import Any


def _register_webhook_routes(app: Any) -> None:
    """GitHub webhook endpoints for auto-analysis on push."""
    from redsl.integrations.webhook import handle_push_webhook

    @app.post("/webhook/push")
    async def github_push_webhook(payload: dict[str, Any]):
        """Handle GitHub push webhook — auto-analyze and alert on degradation."""
        result = await handle_push_webhook(payload)
        return result
