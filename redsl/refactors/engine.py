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
from datetime import datetime, timezone
from pathlib import Path

from redsl.config import RefactorConfig
from redsl.dsl import Decision
from redsl.llm import LLMLayer
from redsl.validation import vallm_bridge

from .models import FileChange, RefactorProposal, RefactorResult
from .prompts import DEFAULT_PROMPT, PROMPTS, build_ecosystem_context

logger = logging.getLogger(__name__)


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

    @staticmethod
    def estimate_confidence(decision: Decision) -> float:
        """T007: Oblicz confidence z metryk — bez potrzeby wywołania LLM.

        Wyższe CC i wyższy score reguły → wyższa pewność że refaktoryzacja jest potrzebna.
        """
        cc = decision.context.get("cyclomatic_complexity", 0)
        score = decision.score

        if cc >= 30:
            cc_conf = 0.90
        elif cc >= 20:
            cc_conf = 0.80
        elif cc >= 15:
            cc_conf = 0.70
        elif cc >= 10:
            cc_conf = 0.60
        else:
            cc_conf = 0.50

        lines = decision.context.get("module_lines", 0)
        if lines > 500:
            cc_conf = min(0.95, cc_conf + 0.05)

        # Blenduj CC-based confidence ze score reguły DSL (znormalizowanym do 0-1)
        score_conf = min(1.0, score / 2.0)
        return round(0.6 * cc_conf + 0.4 * score_conf, 3)

    def generate_proposal(
        self,
        decision: Decision,
        source_code: str,
        model_override: str | None = None,
    ) -> RefactorProposal:
        """Wygeneruj propozycję refaktoryzacji na podstawie decyzji DSL."""

        prompt_template = PROMPTS.get(decision.action, DEFAULT_PROMPT)

        ecosystem_context = build_ecosystem_context(decision.context.get("awareness_context"))

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
        if ecosystem_context:
            prompt = f"{prompt}\n\n{ecosystem_context}"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a strict code refactoring assistant. "
                    "Return ONLY valid JSON. No markdown, no extra text."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response_data = self.llm.call_json(messages, model=model_override)

        # Parsuj odpowiedź
        changes = []
        for ch in response_data.get("changes", []):
            changes.append(
                FileChange(
                    file_path=ch.get("file_path", decision.target_file),
                    refactored_code=ch.get("refactored_code", ""),
                    description=ch.get("description", ""),
                )
            )

        llm_confidence = response_data.get("confidence")
        confidence = (
            float(llm_confidence)
            if llm_confidence is not None and llm_confidence != 0.5
            else self.estimate_confidence(decision)
        )

        proposal = RefactorProposal(
            decision=decision,
            refactor_type=response_data.get("refactor_type", decision.action.value),
            summary=response_data.get("summary", ""),
            changes=changes,
            confidence=confidence,
        )

        logger.info(
            "Generated proposal: %s for %s (confidence=%.2f)",
            proposal.refactor_type,
            decision.target_file,
            proposal.confidence,
        )

        return proposal

    def reflect_on_proposal(
        self,
        proposal: RefactorProposal,
        source_code: str,
        model_override: str | None = None,
    ) -> RefactorProposal:
        """
        Pętla refleksji — agent ocenia i poprawia własną propozycję.
        To jest element „proto-świadomości".
        """
        for round_num in range(self.config.reflection_rounds):
            logger.info(
                "Reflection round %d/%d", round_num + 1, self.config.reflection_rounds
            )

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

            improved_text = self.llm.reflect(changes_text, context, model_override=model_override)
            proposal.reflection_notes += f"\n[Round {round_num + 1}]: {improved_text[:500]}"

            # Jeśli refleksja sugeruje poprawki, spróbuj je zastosować
            if "LGTM" in improved_text or "no issues" in improved_text.lower():
                logger.info("Reflection approved proposal (round %d)", round_num + 1)
                break

        return proposal

    def validate_proposal(self, proposal: RefactorProposal) -> RefactorResult:
        """Waliduj propozycję: syntax check + basic sanity + vallm pipeline (jeśli dostępny)."""
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
                result.warnings.append(
                    f"Very large output for {change.file_path}: {len(code)} chars"
                )

            if "import " not in code and len(code) > 100:
                result.warnings.append(f"No imports found in {change.file_path}")

        # vallm pipeline — głębsza walidacja (imports, security, complexity)
        if len(result.errors) == 0 and vallm_bridge.is_available():
            vallm_result = vallm_bridge.validate_proposal(proposal)
            if not vallm_result["all_valid"]:
                for failed_file in vallm_result["failures"]:
                    result.errors.append(f"vallm: validation failed for {failed_file}")
            elif vallm_result["avg_score"] > 0:
                # Blend vallm score into proposal confidence (punkt 2.3)
                proposal.confidence = vallm_bridge.blend_confidence(
                    proposal.confidence, vallm_result["avg_score"]
                )
                logger.info(
                    "vallm score=%.2f → confidence=%.3f",
                    vallm_result["avg_score"], proposal.confidence,
                )

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
