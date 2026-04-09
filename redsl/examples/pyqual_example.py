from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from redsl.commands.pyqual import PyQualAnalyzer

from ._common import load_example_yaml, parse_scenario, print_banner


def run_pyqual_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("pyqual", scenario=scenario, source=source)

    print_banner(data.get("title", "ReDSL — PyQual"))

    source_files = data.get("source_files", {})
    pyqual_config = data.get("pyqual_config", {})

    with tempfile.TemporaryDirectory(prefix="redsl_pyqual_") as tmpdir:
        project_dir = Path(tmpdir)
        for rel_path, content in source_files.items():
            file_path = project_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        analyzer = PyQualAnalyzer()
        analyzer.config = pyqual_config
        results = analyzer.analyze_project(project_dir)

    summary = results.get("summary", {})
    issues = results.get("issues", {})
    recommendations = results.get("recommendations", [])

    print(f"\n  Pliki:              {summary.get('total_files', 0)}")
    print(f"  Nieużywane importy: {summary.get('unused_imports', 0)}")
    print(f"  Magic numbers:      {summary.get('magic_numbers', 0)}")
    print(f"  Print statements:   {summary.get('print_statements', 0)}")
    print(f"  Brakujące docstringi: {summary.get('missing_docstrings', 0)}")

    unused = issues.get("unused_imports", [])
    if unused:
        print("\n  Nieużywane importy:")
        print("-" * 60)
        for item in unused[:10]:
            print(f"    {item['name']:20s}  {Path(item['file']).name}:{item['line']}")

    magic = issues.get("magic_numbers", [])
    if magic:
        print("\n  Magic numbers:")
        print("-" * 60)
        for item in magic[:10]:
            print(f"    {item['value']:>10}  {Path(item['file']).name}:{item['line']}")

    if recommendations:
        print("\n  Rekomendacje:")
        print("-" * 60)
        for rec in recommendations:
            priority = rec.get("priority", "medium")
            msg = rec.get("message", "")
            print(f"    [{priority:>8s}] {msg}")

    print("\n" + "=" * 60)

    return {"scenario": data, "results": results, "summary": summary}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_pyqual_example(scenario=scenario)


if __name__ == "__main__":
    main()
