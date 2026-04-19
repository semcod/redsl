"""Base class shared by all DirectXRefactorer implementations."""

from __future__ import annotations

from typing import Any


class DirectRefactorBase:
    """Mixin that provides ``get_applied_changes`` for Direct* refactorers."""

    applied_changes: list[dict[str, Any]]

    def get_applied_changes(self) -> list[dict[str, Any]]:
        """Return the list of all changes applied so far."""
        return self.applied_changes
