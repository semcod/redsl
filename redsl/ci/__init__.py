"""
CI/CD integracja — generowanie workflow, bramek jakości, PR botów.

Moduły:
- github_actions — generator plików .github/workflows/ dla GitHub Actions
"""

from __future__ import annotations

from .github_actions import generate_github_workflow, install_github_workflow

__all__ = [
    "generate_github_workflow",
    "install_github_workflow",
]
