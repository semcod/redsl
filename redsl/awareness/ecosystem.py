"""Cross-project ecosystem awareness."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProjectNode:
    """Single project node in the ecosystem graph."""

    path: Path
    name: str
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    health_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "name": self.name,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "health_score": self.health_score,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class EcosystemGraph:
    """Basic ecosystem graph for semcod-style project collections."""

    root: Path
    nodes: dict[str, ProjectNode] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)

    def build(self) -> "EcosystemGraph":
        self.nodes.clear()
        self.edges.clear()

        root = self.root.resolve()
        for candidate in sorted(root.iterdir()):
            if not candidate.is_dir():
                continue
            if not self._is_project_dir(candidate):
                continue
            node = self._build_node(candidate)
            self.nodes[node.name] = node

        self._link_dependencies()
        return self

    def summarize(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "project_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [{"source": src, "target": dst} for src, dst in self.edges],
        }

    def project(self, name: str) -> ProjectNode | None:
        return self.nodes.get(name)

    def impacted_projects(self, project_name: str) -> list[str]:
        node = self.nodes.get(project_name)
        if node is None:
            return []
        impacted = set(node.dependents)
        impacted.update(node.dependencies)
        return sorted(impacted)

    def _build_node(self, path: Path) -> ProjectNode:
        metadata: dict[str, Any] = {"has_todo": (path / "TODO.md").exists()}
        toon_files = [child.name for child in path.iterdir() if child.is_file() and "toon" in child.name.lower()]
        metadata["toon_files"] = toon_files
        dependencies = self._read_dependencies(path)
        health_score = 1.0 if metadata["has_todo"] else 0.5
        health_score += min(1.0, len(toon_files) * 0.1)
        health_score -= min(0.5, len(dependencies) * 0.05)
        return ProjectNode(
            path=path,
            name=path.name,
            dependencies=dependencies,
            dependents=[],
            health_score=round(max(0.0, min(1.0, health_score)), 3),
            metadata=metadata,
        )

    def _link_dependencies(self) -> None:
        for node in self.nodes.values():
            for dependency in node.dependencies:
                if dependency in self.nodes:
                    self.edges.append((node.name, dependency))
                    self.nodes[dependency].dependents.append(node.name)

    def _read_dependencies(self, project_dir: Path) -> list[str]:
        candidates = [project_dir / "goal.yaml", project_dir / "planfile.yaml", project_dir / "project.yaml"]
        dependencies: list[str] = []
        for candidate in candidates:
            if not candidate.exists():
                continue
            text = candidate.read_text(encoding="utf-8")
            for token in self._extract_dependency_tokens(text):
                if token not in dependencies:
                    dependencies.append(token)
        return dependencies

    @staticmethod
    def _extract_dependency_tokens(text: str) -> list[str]:
        tokens: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("-"):
                value = stripped.lstrip("- ").strip()
                if value:
                    tokens.append(value)
            elif ":" in stripped and len(stripped.split(":", 1)[1].strip()) > 0:
                value = stripped.split(":", 1)[1].strip()
                if value and " " not in value and "/" not in value:
                    tokens.append(value)
        return tokens

    @staticmethod
    def _is_project_dir(path: Path) -> bool:
        return any((path / marker).exists() for marker in ("TODO.md", "planfile.yaml", "project_toon.yaml", "analysis.toon.yaml", "goal.yaml"))


__all__ = ["ProjectNode", "EcosystemGraph"]
