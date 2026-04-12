"""Pydantic request/response models for the ReDSL API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    project_dir: str = Field(description="Ścieżka do katalogu projektu")
    project_toon: str | None = Field(None, description="Content pliku project_toon.yaml")
    duplication_toon: str | None = Field(None, description="Content pliku duplication_toon.yaml")
    validation_toon: str | None = Field(None, description="Content pliku validation_toon.yaml")


class RefactorRequest(BaseModel):
    project_dir: str = Field(description="Path to project directory")
    max_actions: int = Field(10, description="Maximum number of actions to apply")
    dry_run: bool = Field(True, description="Show what would be done without applying changes")
    format: str = Field("text", description="Output format: text, yaml, or json")

    model_config = {"populate_by_name": True}


RefactorRequest.model_rebuild()
if not hasattr(RefactorRequest, "model_fields") or "project_path" not in RefactorRequest.model_fields:
    pass


class BatchSemcodRequest(BaseModel):
    semcod_root: str = Field(description="Path to semcod root directory")
    max_actions: int = Field(10, description="Maximum actions per project")
    format: str = Field("text", description="Output format: text, yaml, or json")


class BatchHybridRequest(BaseModel):
    semcod_root: str = Field(description="Path to semcod root directory")
    max_changes: int = Field(30, description="Maximum changes per project")


class DebugConfigRequest(BaseModel):
    show_env: bool = Field(False, description="Show environment variables")


class DebugDecisionsRequest(BaseModel):
    project_path: str = Field(description="Path to project directory")
    limit: int = Field(20, description="Maximum number of decisions to return")


class PyQualAnalyzeRequest(BaseModel):
    project_path: str = Field(description="Path to project directory")
    config: str | None = Field(None, description="Path to pyqual.yaml config")
    format: str = Field("yaml", description="Output format: yaml or json")


class PyQualFixRequest(BaseModel):
    project_path: str = Field(description="Path to project directory")
    config: str | None = Field(None, description="Path to pyqual.yaml config")


class RulesRequest(BaseModel):
    rules: list[dict[str, Any]] = Field(description="List of DSL rules in YAML format")


class ExampleRunRequest(BaseModel):
    name: str = Field(description="Example name: basic_analysis, custom_rules, full_pipeline, memory_learning, api_integration")
    scenario: str = Field("default", description="Scenario variant: default or advanced")


class DecisionResponse(BaseModel):
    rule_name: str
    action: str
    score: float
    target_file: str
    target_function: str | None
    rationale: str


class CycleRequest(BaseModel):
    project_dir: str = Field(description="Path to project directory")
    max_actions: int = Field(3, description="Maximum number of actions to apply")
    clear_history: bool = Field(True, description="Clear decision history before running (avoids duplicate blocks)")
    llm_model: str | None = Field(None, description="Override LLM model (e.g. openrouter/openai/gpt-4o-mini)")


class CycleResponse(BaseModel):
    cycle_number: int
    analysis_summary: str
    decisions_count: int
    proposals_generated: int
    proposals_applied: int
    proposals_rejected: int
    errors: list[str]
    decisions: list[DecisionResponse] = []
    files_modified: list[str] = []
