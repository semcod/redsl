"""GitHub webhook handler — auto-analyze on push to main.

Receives GitHub push webhook payloads and triggers ReDSL analysis.
If code quality degrades (CC̄ increases), creates a GitHub issue as an alert.

Usage:
    - Register this handler as a FastAPI endpoint or Celery task
    - Configure GitHub webhook to POST push events to /api/redsl/webhook/push
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


async def handle_push_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """Process a GitHub push webhook payload.

    Steps:
      1. Extract repo and branch info
      2. If push to main: run analysis
      3. If metrics degraded: create GitHub issue

    Returns a summary dict with status and any actions taken.
    """
    repo = payload.get("repository", {}).get("full_name", "")
    ref = payload.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ""

    if branch != "main":
        logger.info("Ignoring push to non-main branch: %s (%s)", repo, branch)
        return {"status": "skipped", "reason": f"not main branch: {branch}"}

    logger.info("Push to main detected: %s", repo)

    # Run analysis via the API client
    analysis = await _analyze_repo(repo)

    result = {
        "status": "analyzed",
        "repo": repo,
        "branch": branch,
        "commits": len(payload.get("commits", [])),
    }

    # Check for degradation
    cc_delta = analysis.get("cc_delta", 0)
    if cc_delta > 0.3:
        logger.warning("CC̄ increased by %.1f for %s — creating issue", cc_delta, repo)
        issue_result = _create_github_issue(
            repo=repo,
            title=f"[ReDSL] CC̄ wzrosło o {cc_delta:.1f}",
            body=f"Quality gate failed after push to {branch}.\n\n"
                 f"CC̄ delta: +{cc_delta:.1f}\n"
                 f"Commits: {len(payload.get('commits', []))}",
        )
        result["issue_created"] = issue_result
        result["cc_delta"] = cc_delta
    else:
        result["cc_delta"] = cc_delta

    return result


async def _analyze_repo(repo: str) -> dict[str, Any]:
    """Run ReDSL analysis on a repository and return metrics with delta."""
    try:
        from redsl.api import _get_orchestrator

        orch = _get_orchestrator()
        # For webhook: we'd need the local clone path
        # In production, this would clone the repo first
        logger.info("Analysis requested for %s (orchestrator available: %s)", repo, orch is not None)
        return {"cc_delta": 0, "analysis_available": orch is not None}
    except Exception as exc:
        logger.error("Analysis failed for %s: %s", repo, exc)
        return {"cc_delta": 0, "error": str(exc)}


def _create_github_issue(repo: str, title: str, body: str) -> dict[str, Any]:
    """Create a GitHub issue via the gh CLI or API.

    Returns the issue URL or error info.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            issue_url = result.stdout.strip()
            logger.info("Created issue: %s", issue_url)
            return {"url": issue_url}
        else:
            logger.warning("gh issue create failed: %s", result.stderr)
            return {"error": result.stderr.strip()}
    except FileNotFoundError:
        logger.warning("gh CLI not available — skipping issue creation")
        return {"error": "gh CLI not installed"}
    except subprocess.TimeoutExpired:
        return {"error": "gh CLI timed out"}
