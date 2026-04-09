"""Output formatters for reDSL."""

from __future__ import annotations

import json
import yaml
from typing import Any, Dict, List
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax

console = Console(stderr=True)


def format_refactor_plan(
    decisions: List[Any], 
    format: str = "text",
    analysis: Any = None
) -> str:
    """Format refactoring plan in specified format."""
    if format == "yaml":
        return _format_yaml(decisions, analysis)
    elif format == "json":
        return _format_json(decisions, analysis)
    else:
        return _format_text(decisions, analysis)


def _format_yaml(decisions: List[Any], analysis: Any = None) -> str:
    """Format as YAML."""
    data = {
        "refactoring_plan": {
            "timestamp": _get_timestamp(),
            "analysis": _serialize_analysis(analysis) if analysis else None,
            "decisions": [_serialize_decision(d) for d in decisions],
            "summary": {
                "total_decisions": len(decisions),
                "decision_types": _count_decision_types(decisions),
                "estimated_impact": sum(d.score for d in decisions)
            }
        }
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def _format_json(decisions: List[Any], analysis: Any = None) -> str:
    """Format as JSON."""
    data = {
        "refactoring_plan": {
            "timestamp": _get_timestamp(),
            "analysis": _serialize_analysis(analysis) if analysis else None,
            "decisions": [_serialize_decision(d) for d in decisions],
            "summary": {
                "total_decisions": len(decisions),
                "decision_types": _count_decision_types(decisions),
                "estimated_impact": sum(d.score for d in decisions)
            }
        }
    }
    return json.dumps(data, indent=2, default=str)


def _format_text(decisions: List[Any], analysis: Any = None) -> str:
    """Format as rich text."""
    output = []
    
    # Header
    output.append("\n=== REFACTORING PLAN ===\n")
    
    # Analysis summary
    if analysis:
        output.append(f"Analysis complete: {analysis.total_files} files, "
                     f"{analysis.total_lines} lines, avg CC={analysis.avg_cc:.1f}, "
                     f"{analysis.critical_count} critical\n")
    
    # Decision summary
    decision_types = _count_decision_types(decisions)
    output.append(f"Decision types: {decision_types}\n")
    output.append(f"Evaluated {len(analysis.metrics) if analysis else 'N/A'} contexts → {len(decisions)} decisions\n")
    
    # Top decisions table
    if decisions:
        table = Table(title=f"Top {min(5, len(decisions))} refactoring decisions")
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Decision", style="magenta")
        table.add_column("Rule", style="green")
        table.add_column("Target", style="yellow")
        table.add_column("Score", style="red", justify="right")
        table.add_column("Confidence", style="blue", justify="right")
        
        for i, decision in enumerate(decisions[:5], 1):
            table.add_row(
                str(i),
                decision.action.value,
                decision.rule.name if hasattr(decision, 'rule') and decision.rule else "N/A",
                str(decision.target_file),
                f"{decision.score:.2f}",
                f"{getattr(decision, 'confidence', 0):.2f}"
            )
        
        # Capture table output
        with console.capture() as capture:
            console.print(table)
        output.append(capture.get())
    
    # Detailed decisions
    for i, decision in enumerate(decisions[:5], 1):
        output.append(f"\n{i}. Decision: {decision.action.value}")
        output.append(f"   Rule: {decision.rule.name if hasattr(decision, 'rule') and decision.rule else 'N/A'}")
        output.append(f"   Target: {decision.target_file}")
        output.append(f"   Score: {decision.score:.2f}")
        if hasattr(decision, 'rationale') and decision.rationale:
            output.append(f"   Rationale: {decision.rationale}")
        if hasattr(decision, 'confidence'):
            output.append(f"   Confidence (metric): {decision.confidence:.2f}")
    
    return "\n".join(output)


def _serialize_analysis(analysis: Any) -> Dict[str, Any]:
    """Serialize analysis object to dict."""
    if not analysis:
        return None
    
    return {
        "project_name": getattr(analysis, "project_name", getattr(analysis, "name", "Unknown")),
        "total_files": getattr(analysis, "total_files", 0),
        "total_lines": getattr(analysis, "total_lines", 0),
        "avg_complexity": getattr(analysis, "avg_cc", getattr(analysis, "avg_complexity", 0)),
        "critical_count": getattr(analysis, "critical_count", 0),
        "alerts_count": len(getattr(analysis, "alerts", [])),
        "metrics_count": len(getattr(analysis, "metrics", [])),
        "metrics": [
            {
                "file": str(m.file_path),
                "name": m.function_name,
                "cc": m.cyclomatic_complexity,
                "loc": m.module_lines
            } for m in list(getattr(analysis, "metrics", []))[:10]
        ]
    }


def _serialize_decision(decision: Any) -> Dict[str, Any]:
    """Serialize decision object to dict."""
    data = {
        "action": decision.action.value if hasattr(decision, 'action') else str(decision.action),
        "target_path": str(decision.target_file),
        "score": decision.score,
    }
    
    if hasattr(decision, 'rule') and decision.rule:
        data["rule"] = decision.rule.name
    
    if hasattr(decision, 'rationale'):
        data["rationale"] = decision.rationale
    
    if hasattr(decision, 'confidence'):
        data["confidence"] = decision.confidence
    
    if hasattr(decision, 'metadata'):
        data["metadata"] = decision.metadata
    
    return data


def _count_decision_types(decisions: List[Any]) -> Dict[str, int]:
    """Count decisions by type."""
    types = {}
    for decision in decisions:
        action = decision.action.value if hasattr(decision, 'action') else str(decision.action)
        types[action] = types.get(action, 0) + 1
    return types


def _get_timestamp() -> str:
    """Get current timestamp."""
    from datetime import datetime
    return datetime.now().isoformat()


def format_batch_results(results: List[Dict[str, Any]], format: str = "text") -> str:
    """Format batch processing results."""
    if format == "yaml":
        return yaml.dump({"batch_results": results}, default_flow_style=False, sort_keys=False)
    elif format == "json":
        return json.dumps({"batch_results": results}, indent=2, default=str)
    else:
        # Rich text format
        output = ["\n=== BATCH PROCESSING RESULTS ===\n"]
        
        for i, result in enumerate(results, 1):
            output.append(f"{i}. Project: {result.get('project_name', 'Unknown')}")
            output.append(f"   Status: {result.get('status', 'Unknown')}")
            output.append(f"   Files processed: {result.get('files_processed', 0)}")
            output.append(f"   Changes applied: {result.get('changes_applied', 0)}")
            if result.get('error'):
                output.append(f"   Error: {result['error']}")
            output.append("")
        
        # Summary
        total = len(results)
        successful = sum(1 for r in results if r.get('status') == 'success')
        output.append(f"\nSummary: {successful}/{total} projects processed successfully")
        
        return "\n".join(output)


def format_cycle_report_yaml(report: Any, decisions: List[Any] = None, analysis: Any = None) -> str:
    """Format full cycle report as YAML for stdout."""
    data: Dict[str, Any] = {
        "redsl_report": {
            "timestamp": _get_timestamp(),
            "cycle": report.cycle_number,
            "analysis": _serialize_analysis(analysis) if analysis else {
                "summary": report.analysis_summary,
            },
            "plan": {
                "total_decisions": report.decisions_count,
                "decisions": [_serialize_decision(d) for d in (decisions or [])],
            },
            "execution": {
                "proposals_generated": report.proposals_generated,
                "proposals_applied": report.proposals_applied,
                "proposals_rejected": report.proposals_rejected,
                "success_rate": (
                    round(report.proposals_applied / report.proposals_generated, 2)
                    if report.proposals_generated > 0 else 0.0
                ),
                "results": [_serialize_result(r) for r in (report.results or [])],
            },
            "errors": report.errors if report.errors else [],
        }
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def format_cycle_report_markdown(
    report: Any,
    decisions: List[Any] | None = None,
    analysis: Any = None,
    project_path: Path | None = None,
    log_file: Path | None = None,
    dry_run: bool = False,
) -> str:
    """Format a refactor cycle as a Markdown report."""
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    decision_list = decisions or []
    lines: list[str] = []

    title = "reDSL Refactor Plan" if dry_run else "reDSL Refactor Report"
    lines.extend([
        f"# {title}",
        "",
        f"> Generated: **{now}**  ",
    ])
    if project_path is not None:
        lines.append(f"> Project: `{project_path}`  ")
    lines.append(f"> Mode: **{'dry-run' if dry_run else 'executed'}**  ")
    if log_file is not None:
        lines.append(f"> Log file: `{log_file}`  ")
    if report is not None and hasattr(report, "cycle_number"):
        lines.append(f"> Cycle: **{report.cycle_number}**  ")
    lines.append("")
    lines.extend(["---", ""])

    lines.append("## Summary")
    lines.append("")
    if analysis is not None:
        serialized_analysis = _serialize_analysis(analysis) or {}
        lines.append(f"- Project: `{serialized_analysis.get('project_name', 'Unknown')}`")
        lines.append(
            f"- Files: **{serialized_analysis.get('total_files', 0)}** | "
            f"Lines: **{serialized_analysis.get('total_lines', 0)}** | "
            f"Avg CC: **{serialized_analysis.get('avg_complexity', 0)}**"
        )
        lines.append(
            f"- Critical: **{serialized_analysis.get('critical_count', 0)}** | "
            f"Alerts: **{serialized_analysis.get('alerts_count', 0)}**"
        )
    lines.append(f"- Decisions selected: **{len(decision_list)}**")
    if report is not None and not dry_run:
        lines.append(f"- Proposals generated: **{getattr(report, 'proposals_generated', 0)}**")
        lines.append(f"- Proposals applied: **{getattr(report, 'proposals_applied', 0)}**")
        lines.append(f"- Proposals rejected: **{getattr(report, 'proposals_rejected', 0)}**")
        lines.append(f"- Errors: **{len(getattr(report, 'errors', []))}**")
    lines.append("")

    if decision_list:
        lines.append("## Top Decisions")
        lines.append("")
        for index, decision in enumerate(decision_list[:10], 1):
            action_obj = getattr(decision, "action", None)
            if action_obj is None:
                action = getattr(decision, "rule_name", "unknown")
            else:
                action = action_obj.value if hasattr(action_obj, "value") else str(action_obj)
            target = getattr(decision, "target_file", None)
            rule = getattr(getattr(decision, "rule", None), "name", None)
            if target is not None:
                lines.append(f"{index}. **{action}** → `{target}`")
            else:
                lines.append(f"{index}. **{action}**")
            lines.append(f"   - Score: `{getattr(decision, 'score', 0):.2f}`")
            if rule:
                lines.append(f"   - Rule: `{rule}`")
            rationale = getattr(decision, "rationale", None)
            if rationale:
                lines.append(f"   - Rationale: {rationale}")
            confidence = getattr(decision, "confidence", None)
            if confidence is not None:
                lines.append(f"   - Confidence: `{confidence:.2f}`")
        lines.append("")

    if report is not None and not dry_run:
        lines.append("## Execution Results")
        lines.append("")
        for index, result in enumerate(getattr(report, "results", [])[:10], 1):
            serialized = _serialize_result(result)
            lines.append(f"{index}. **{serialized.get('action', 'direct_refactor')}**")
            lines.append(f"   - Target: `{serialized.get('target', 'N/A')}`")
            lines.append(f"   - Applied: `{serialized.get('applied', False)}`")
            lines.append(f"   - Validated: `{serialized.get('validated', False)}`")
            if serialized.get("confidence") is not None:
                lines.append(f"   - Confidence: `{serialized['confidence']:.2f}`")
            if serialized.get("summary"):
                lines.append(f"   - Summary: {serialized['summary']}")
            if serialized.get("errors"):
                lines.append(f"   - Errors: {', '.join(serialized['errors'])}")
        lines.append("")

        if getattr(report, "errors", None):
            lines.append("## Errors")
            lines.append("")
            for error in report.errors:
                lines.append(f"- {error}")
            lines.append("")

    lines.extend([
        "---",
        "",
        "_Report generated by [reDSL](https://github.com/wronai/redsl)_",
    ])
    return "\n".join(lines)


def format_batch_report_markdown(report: Dict[str, Any], root: Path, title: str) -> str:
    """Format a batch run report as Markdown."""
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    details = list(report.get("project_details", []))

    def _as_int(value: Any, fallback: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    total_before = _as_int(report.get("total_before"), sum(_as_int(d.get("before_issues")) for d in details))
    total_after = _as_int(report.get("total_after"), sum(_as_int(d.get("after_issues")) for d in details))
    total_applied = _as_int(report.get("total_applied"), sum(_as_int(d.get("applied", d.get("changes_applied"))) for d in details))
    total_decisions = _as_int(report.get("total_decisions"), sum(_as_int(d.get("decisions", d.get("quality_decisions"))) for d in details))
    total_errors = _as_int(report.get("total_errors"), sum(_as_int(d.get("errors")) for d in details))

    lines: list[str] = [
        f"# {title}",
        "",
        f"> Generated: **{now}**  ",
        f"> Root: `{root}`  ",
        f"> Projects processed: **{report.get('projects_processed', len(details))}**  ",
        f"> Decisions: **{total_decisions}**  ",
        f"> Applied: **{total_applied}**  ",
        f"> Errors: **{total_errors}**  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- TODO issues before: **{total_before}**",
        f"- TODO issues after: **{total_after}**",
        f"- TODO reduction: **{total_before - total_after}**",
        f"- Decisions: **{total_decisions}**",
        f"- Applied changes: **{total_applied}**",
        f"- Errors: **{total_errors}**",
        "",
    ]

    if details:
        lines.extend([
            "## Projects",
            "",
            "| Project | Decisions | Applied | TODO before | TODO after | Δ TODO | Errors |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ])
        for detail in details:
            before = _as_int(detail.get("before_issues"), 0)
            after = _as_int(detail.get("after_issues"), 0)
            reduction = detail.get("todo_reduction")
            if reduction is None:
                reduction = before - after
            decisions_count = _as_int(detail.get("decisions", detail.get("quality_decisions")))
            applied = _as_int(detail.get("applied", detail.get("changes_applied")))
            errors = _as_int(detail.get("errors"))
            lines.append(
                f"| `{detail.get('name', detail.get('project', 'Unknown'))}` | "
                f"{decisions_count} | {applied} | {before} | {after} | {reduction} | {errors} |"
            )
        lines.append("")

    improvements = sorted(
        details,
        key=lambda item: _as_int(item.get("todo_reduction"), _as_int(item.get("before_issues")) - _as_int(item.get("after_issues"))),
        reverse=True,
    )
    improvements = [
        item for item in improvements
        if _as_int(item.get("todo_reduction"), _as_int(item.get("before_issues")) - _as_int(item.get("after_issues"))) > 0
    ]
    if improvements:
        lines.extend(["## Top improvements", ""])
        for detail in improvements[:5]:
            before = _as_int(detail.get("before_issues"), 0)
            after = _as_int(detail.get("after_issues"), 0)
            reduction = _as_int(detail.get("todo_reduction"), before - after)
            lines.append(
                f"- `{detail.get('name', detail.get('project', 'Unknown'))}`: **{reduction}** fewer TODOs "
                f"({before} → {after})"
            )
        lines.append("")

    errors = [detail for detail in details if _as_int(detail.get("errors")) > 0]
    if errors:
        lines.extend(["## Errors", ""])
        for detail in errors:
            lines.append(f"- `{detail.get('name', detail.get('project', 'Unknown'))}`: {detail.get('errors')} errors")
        lines.append("")

    lines.extend([
        "---",
        "",
        "_Report generated by [reDSL](https://github.com/wronai/redsl)_",
    ])
    return "\n".join(lines)


def format_plan_yaml(decisions: List[Any], analysis: Any = None) -> str:
    """Format dry-run plan as YAML for stdout."""
    data: Dict[str, Any] = {
        "redsl_plan": {
            "timestamp": _get_timestamp(),
            "analysis": _serialize_analysis(analysis) if analysis else None,
            "decisions": [_serialize_decision(d) for d in decisions],
            "summary": {
                "total_decisions": len(decisions),
                "decision_types": _count_decision_types(decisions),
                "estimated_impact": round(sum(d.score for d in decisions), 2),
            },
        }
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _serialize_result(result: Any) -> Dict[str, Any]:
    """Serialize a RefactorResult to dict."""
    entry: Dict[str, Any] = {
        "applied": result.applied,
        "validated": result.validated,
    }
    if result.errors:
        entry["errors"] = result.errors
    if result.warnings:
        entry["warnings"] = result.warnings

    proposal = result.proposal
    if proposal is not None:
        entry["action"] = proposal.refactor_type
        entry["target"] = proposal.decision.target_file if proposal.decision else None
        entry["confidence"] = round(proposal.confidence, 2)
        entry["summary"] = proposal.summary
        if proposal.changes:
            entry["files_changed"] = [c.file_path for c in proposal.changes]
    else:
        # Direct refactor — no proposal object
        entry["action"] = "direct_refactor"
    return entry


def format_debug_info(info: Dict[str, Any], format: str = "text") -> str:
    """Format debug information."""
    if format == "yaml":
        return yaml.dump(info, default_flow_style=False, sort_keys=False)
    elif format == "json":
        return json.dumps(info, indent=2, default=str)
    else:
        # Rich text format with syntax highlighting
        output = ["\n=== DEBUG INFORMATION ===\n"]
        
        for key, value in info.items():
            if isinstance(value, (dict, list)):
                output.append(f"{key}:")
                if format == "text":
                    value_str = json.dumps(value, indent=2, default=str)
                    syntax = Syntax(value_str, "json", theme="monokai", line_numbers=True)
                    with console.capture() as capture:
                        console.print(syntax)
                    output.append(capture.get())
            else:
                output.append(f"{key}: {value}")
        
        return "\n".join(output)
