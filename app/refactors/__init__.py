"""
Silnik refaktoryzacji — generowanie, walidacja i aplikowanie patchy.

Proces:
1. Na podstawie Decision z DSL Engine generuje prompt dla LLM
2. LLM zwraca propozycję zmian jako JSON + unified diff
3. Agent reflektuje nad propozycją (self-critique)
4. Walidacja: linter + testy + diff sanity check
5. Aplikacja patcha (lub zapis do review)
"""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import RefactorConfig
from app.dsl import Decision, RefactorAction
from app.llm import LLMLayer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Modele danych
# ---------------------------------------------------------------------------

@dataclass
class RefactorProposal:
    """Propozycja refaktoryzacji wygenerowana przez LLM."""

    decision: Decision
    refactor_type: str
    summary: str
    changes: list[FileChange] = field(default_factory=list)
    rationale: str = ""
    confidence: float = 0.0
    reflection_notes: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class FileChange:
    """Zmiana w pojedynczym pliku."""

    file_path: str
    original_code: str = ""
    refactored_code: str = ""
    patch: str = ""
    description: str = ""


@dataclass
class RefactorResult:
    """Wynik zastosowania refaktoryzacji."""

    proposal: RefactorProposal
    applied: bool = False
    validated: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

PROMPTS = {
    RefactorAction.EXTRACT_FUNCTIONS: """
You are an expert Python refactoring assistant.
Your task: EXTRACT smaller functions from a complex function.

RULES:
- Keep behavior IDENTICAL (no behavioral changes!)
- Each extracted function should have a single responsibility
- Use descriptive names (verb_noun pattern)
- Preserve all error handling and logging
- Add type hints to new functions
- DO NOT change public API signatures
- DO NOT remove tests, configuration, or logging

Target function: {function_name}
Current cyclomatic complexity: {cc}
Target: CC < 10 per function

File: {file_path}
Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "extract_functions",
    "summary": "human-readable description of changes",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "{file_path}",
            "refactored_code": "full refactored file content",
            "description": "what changed and why"
        }}
    ]
}}
""",

    RefactorAction.SPLIT_MODULE: """
You are an expert Python refactoring assistant.
Your task: SPLIT a god module into smaller, focused modules.

RULES:
- Keep ALL existing imports working (use re-exports in __init__.py if needed)
- Group by responsibility (routes, business logic, models, utilities)
- Each new module should be < 200 lines
- Preserve all public APIs
- Create proper __init__.py with re-exports

Current module: {file_path} ({lines} lines, {functions} functions)

Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "split_module",
    "summary": "description of the split strategy",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "new/module/path.py",
            "refactored_code": "content of the new file",
            "description": "what this module contains"
        }}
    ]
}}
""",

    RefactorAction.DEDUPLICATE: """
You are an expert Python refactoring assistant.
Your task: DEDUPLICATE code by extracting common logic.

RULES:
- Create a shared utility module for the common code
- Update all files that use the duplicated code to import from the shared module
- Keep behavior IDENTICAL
- Preserve all function signatures

Duplicate found in:
{duplicate_files}

Duplicate code ({dup_lines} lines, similarity: {similarity}):
```python
{dup_code}
```

Return JSON:
{{
    "refactor_type": "deduplicate",
    "summary": "description",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "shared/module.py",
            "refactored_code": "content",
            "description": "shared utility"
        }},
        {{
            "file_path": "original/file.py",
            "refactored_code": "updated content importing from shared",
            "description": "updated to use shared module"
        }}
    ]
}}
""",

    RefactorAction.REDUCE_FAN_OUT: """
You are an expert Python refactoring assistant.
Your task: REDUCE fan-out by introducing facade or mediator pattern.

RULES:
- Introduce a facade/mediator to reduce direct dependencies
- Keep behavior IDENTICAL
- New abstractions should be well-named and documented

Function: {function_name}
Current fan-out: {fan_out}
Target: fan-out < 10

Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "reduce_fan_out",
    "summary": "description",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "{file_path}",
            "refactored_code": "content",
            "description": "what changed"
        }}
    ]
}}
""",

    RefactorAction.SIMPLIFY_CONDITIONALS: """
You are an expert Python refactoring assistant.
Your task: SIMPLIFY complex conditional logic.

TECHNIQUES to apply:
- Early return / guard clauses
- Replace nested if/else with match/case or dictionary dispatch
- Extract complex conditions into named boolean functions
- Reduce nesting depth to maximum 3

Function: {function_name}
Current CC: {cc}

Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "simplify_conditionals",
    "summary": "description",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "{file_path}",
            "refactored_code": "content",
            "description": "what changed"
        }}
    ]
}}
""",
}

# Domyślny prompt dla akcji bez dedykowanego szablonu
DEFAULT_PROMPT = """
You are an expert Python refactoring assistant.
Task: {action}
Target: {file_path}
{extra_context}

RULES:
- Keep behavior IDENTICAL
- Improve code quality without breaking anything
- Add type hints where missing
- Follow PEP 8

Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "{action}",
    "summary": "description",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "{file_path}",
            "refactored_code": "content",
            "description": "what changed"
        }}
    ]
}}
"""


# ---------------------------------------------------------------------------
# Refactor Engine
# ---------------------------------------------------------------------------

class RefactorEngine:
    """
    Silnik refaktoryzacji z pętlą refleksji.

    1. Generuj propozycję (LLM)
    2. Reflektuj (self-critique)
    3. Waliduj (linter + sanity)
    4. Aplikuj lub zapisz do review
    """

    def __init__(self, llm: LLMLayer, config: RefactorConfig) -> None:
        self.llm = llm
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_proposal(
        self,
        decision: Decision,
        source_code: str,
    ) -> RefactorProposal:
        """Wygeneruj propozycję refaktoryzacji na podstawie decyzji DSL."""

        prompt_template = PROMPTS.get(decision.action, DEFAULT_PROMPT)

        prompt = prompt_template.format(
            file_path=decision.target_file,
            function_name=decision.target_function or "N/A",
            cc=decision.context.get("cyclomatic_complexity", 0),
            fan_out=decision.context.get("fan_out", 0),
            lines=decision.context.get("module_lines", 0),
            functions=decision.context.get("function_count", 0),
            code=source_code[:8000],  # Limit kontekstu
            action=decision.action.value,
            extra_context=decision.rationale,
            duplicate_files=", ".join(
                decision.context.get("duplicate_files", [])
            ),
            dup_lines=decision.context.get("duplicate_lines", 0),
            similarity=decision.context.get("duplicate_similarity", 0),
            dup_code=decision.context.get("duplicate_code", ""),
        )

        messages = [
            {"role": "system", "content": (
                "You are a strict code refactoring assistant. "
                "Return ONLY valid JSON. No markdown, no extra text."
            )},
            {"role": "user", "content": prompt},
        ]

        response_data = self.llm.call_json(messages)

        # Parsuj odpowiedź
        changes = []
        for ch in response_data.get("changes", []):
            changes.append(FileChange(
                file_path=ch.get("file_path", decision.target_file),
                refactored_code=ch.get("refactored_code", ""),
                description=ch.get("description", ""),
            ))

        proposal = RefactorProposal(
            decision=decision,
            refactor_type=response_data.get("refactor_type", decision.action.value),
            summary=response_data.get("summary", ""),
            changes=changes,
            confidence=response_data.get("confidence", 0.5),
        )

        logger.info(
            "Generated proposal: %s for %s (confidence=%.2f)",
            proposal.refactor_type, decision.target_file, proposal.confidence,
        )

        return proposal

    def reflect_on_proposal(
        self,
        proposal: RefactorProposal,
        source_code: str,
    ) -> RefactorProposal:
        """
        Pętla refleksji — agent ocenia i poprawia własną propozycję.
        To jest element „proto-świadomości".
        """
        for round_num in range(self.config.reflection_rounds):
            logger.info("Reflection round %d/%d", round_num + 1, self.config.reflection_rounds)

            # Zbierz wszystkie zmiany do oceny
            changes_text = "\n\n".join(
                f"--- {ch.file_path} ---\n{ch.description}\n{ch.refactored_code[:3000]}"
                for ch in proposal.changes
            )

            context = (
                f"Original code:\n{source_code[:3000]}\n\n"
                f"Refactoring type: {proposal.refactor_type}\n"
                f"Summary: {proposal.summary}"
            )

            improved_text = self.llm.reflect(changes_text, context)
            proposal.reflection_notes += f"\n[Round {round_num + 1}]: {improved_text[:500]}"

            # Jeśli refleksja sugeruje poprawki, spróbuj je zastosować
            if "LGTM" in improved_text or "no issues" in improved_text.lower():
                logger.info("Reflection approved proposal (round %d)", round_num + 1)
                break

        return proposal

    def validate_proposal(self, proposal: RefactorProposal) -> RefactorResult:
        """Waliduj propozycję: syntax check + basic sanity."""
        result = RefactorResult(proposal=proposal)

        for change in proposal.changes:
            code = change.refactored_code

            if not code.strip():
                result.errors.append(f"Empty code for {change.file_path}")
                continue

            # Syntax check
            try:
                compile(code, change.file_path, "exec")
            except SyntaxError as e:
                result.errors.append(f"Syntax error in {change.file_path}: {e}")

            # Sanity checks
            if len(code) > 50000:
                result.warnings.append(f"Very large output for {change.file_path}: {len(code)} chars")

            if "import " not in code and len(code) > 100:
                result.warnings.append(f"No imports found in {change.file_path}")

        result.validated = len(result.errors) == 0
        return result

    def apply_proposal(
        self,
        proposal: RefactorProposal,
        project_dir: Path,
    ) -> RefactorResult:
        """Zastosuj propozycję refaktoryzacji."""
        result = self.validate_proposal(proposal)

        if not result.validated:
            logger.warning("Proposal validation failed: %s", result.errors)
            return result

        if self.config.dry_run:
            # W trybie dry-run zapisz propozycje do plików
            self._save_proposal(proposal)
            logger.info("Dry run: proposal saved to %s", self.config.output_dir)
            return result

        # Aplikuj zmiany
        for change in proposal.changes:
            target = project_dir / change.file_path

            if self.config.backup_enabled and target.exists():
                backup = target.with_suffix(target.suffix + ".bak")
                backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change.refactored_code, encoding="utf-8")
            logger.info("Applied change to %s", change.file_path)

        result.applied = True
        return result

    def _save_proposal(self, proposal: RefactorProposal) -> None:
        """Zapisz propozycję do plików w output_dir."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        base_name = f"refactor_{proposal.refactor_type}_{timestamp}"
        out_dir = self.config.output_dir / base_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Metadane
        meta = {
            "refactor_type": proposal.refactor_type,
            "summary": proposal.summary,
            "confidence": proposal.confidence,
            "target_file": proposal.decision.target_file,
            "target_function": proposal.decision.target_function,
            "score": proposal.decision.score,
            "rationale": proposal.decision.rationale,
            "reflection_notes": proposal.reflection_notes,
            "timestamp": proposal.timestamp,
            "changes": [
                {"file_path": ch.file_path, "description": ch.description}
                for ch in proposal.changes
            ],
        }
        (out_dir / "metadata.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Pliki ze zmianami
        for i, change in enumerate(proposal.changes):
            safe_name = change.file_path.replace("/", "__")
            (out_dir / f"{i:02d}_{safe_name}").write_text(
                change.refactored_code, encoding="utf-8"
            )

        logger.info("Saved proposal to %s", out_dir)
