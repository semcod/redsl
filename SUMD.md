# Ze źródeł

ReDSL — Refactor + DSL + Self-Learning. LLM-powered autonomous code refactoring.

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Intent](#intent)

## Metadata

- **name**: `redsl`
- **version**: `1.2.33`
- **python_requires**: `>=3.11`
- **license**: Apache-2.0
- **ai_model**: `openrouter/openai/gpt-5-mini`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, requirements.txt, Taskfile.yml, Makefile, app.doql.css, goal.yaml, .env.example, Dockerfile, docker-compose.yml, src(5 mod), project/(1 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.css`)

```css markpact:doql path=app.doql.css
app {
  name: "redsl";
  version: "1.2.28";
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="redsl"] {

}

workflow[name="install"] {
  trigger: "manual";
  step-1: run cmd=$(PIP) install -r requirements.txt;
}

workflow[name="dev-install"] {
  trigger: "manual";
  step-1: run cmd=$(PIP) install -r requirements.txt;
  step-2: run cmd=$(PIP) install -e ".[dev]";
}

workflow[name="test"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -v -m "not slow";
}

workflow[name="test-fast"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -q -m "not slow and not integration and not e2e";
}

workflow[name="test-all"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -v;
}

workflow[name="lint"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff check redsl/ tests/;
}

workflow[name="type-check"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m mypy redsl/;
}

workflow[name="format"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff format redsl/ tests/;
  step-2: run cmd=$(PYTHON) -m ruff check --fix redsl/ tests/;
}

workflow[name="format-check"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff format --check redsl/ tests/;
}

workflow[name="docker-up"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) up -d;
}

workflow[name="docker-down"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) down;
}

workflow[name="docker-build"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) build;
}

workflow[name="run"] {
  trigger: "manual";
  step-1: depend target=docker-up;
}

workflow[name="run-local"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000;
}

workflow[name="clean"] {
  trigger: "manual";
  step-1: run cmd=find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true;
  step-2: run cmd=find . -type f -name "*.pyc" -delete 2>/dev/null || true;
  step-3: run cmd=find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true;
  step-4: run cmd=find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true;
  step-5: run cmd=rm -rf refactor_output/ 2>/dev/null || true;
}

workflow[name="fmt"] {
  trigger: "manual";
  step-1: run cmd=ruff format .;
}

workflow[name="build"] {
  trigger: "manual";
  step-1: run cmd=python -m build;
}

workflow[name="health"] {
  trigger: "manual";
  step-1: run cmd=docker compose ps;
  step-2: run cmd=docker compose exec app echo "Health check passed";
}

workflow[name="up"] {
  trigger: "manual";
  step-1: run cmd=docker compose up -d;
}

workflow[name="down"] {
  trigger: "manual";
  step-1: run cmd=docker compose down;
}

workflow[name="logs"] {
  trigger: "manual";
  step-1: run cmd=docker compose logs -f;
}

workflow[name="ps"] {
  trigger: "manual";
  step-1: run cmd=docker compose ps;
}

workflow[name="import-makefile-hint"] {
  trigger: "manual";
  step-1: run cmd=echo 'Run: taskfile import Makefile to import existing targets.';
}

workflow[name="help"] {
  trigger: "manual";
  step-1: run cmd=echo \"Dost\u0119pne komendy:\; 
  step-2: run cmd=echo \"  install       - Instalacja zale\u017Cno\u015Bci produkcyjnych\; 
  step-3: run cmd=echo \"  dev-install   - Instalacja zale\u017Cno\u015Bci deweloperskich\; 
  step-4: run cmd=echo \"  test          - Uruchomienie test\xF3w pytest (bez slow)\; 
  step-5: run cmd=echo "  test-fast     - Szybkie testy (bez slow/integration/e2e)";
  step-6: run cmd=echo \"  test-all      - Wszystkie testy w\u0142\u0105cznie z slow\; 
  step-7: run cmd=echo "  lint          - Sprawdzenie lintingu ruff";
  step-8: run cmd=echo \"  type-check    - Sprawdzenie typ\xF3w mypy\; 
  step-9: run cmd=echo "  format        - Formatowanie kodu ruff";
  step-10: run cmd=echo "  format-check  - Sprawdzenie formatowania kodu";
  step-11: run cmd=echo \"  docker-up     - Uruchomienie us\u0142ug Docker\; 
  step-12: run cmd=echo \"  docker-down   - Zatrzymanie us\u0142ug Docker\; 
  step-13: run cmd=echo \"  docker-build  - Budowanie obraz\xF3w Docker\; 
  step-14: run cmd=echo "  run           - Uruchomienie aplikacji w Docker";
  step-15: run cmd=echo "  run-local     - Uruchomienie aplikacji lokalnie";
  step-16: run cmd=echo \"  clean         - Czyszczenie plik\xF3w tymczasowych\; 
}

deploy {
  target: docker-compose;
  compose_file: docker-compose.yml;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: ".env";
}

workflow[name="all"] {
  trigger: "manual";
  step-1: run cmd=taskfile run install;
  step-2: run cmd=taskfile run lint;
  step-3: run cmd=taskfile run test;
}
```

### Source Modules

- `redsl.config`
- `redsl.consciousness_loop`
- `redsl.history`
- `redsl.main`
- `redsl.orchestrator`

## Interfaces

### CLI Entry Points

- `redsl`

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml markpact:taskfile path=Taskfile.yml
version: '1'
name: redsl
description: Minimal Taskfile
variables:
  APP_NAME: redsl
environments:
  local:
    container_runtime: docker
    compose_command: docker compose
pipeline:
  python_version: "3.12"
  runner_image: ubuntu-latest
  branches: [main]
  cache: [~/.cache/pip]
  artifacts: [dist/]

  stages:
    - name: lint
      tasks: [lint]

    - name: test
      tasks: [test]

    - name: build
      tasks: [build]
      when: "branch:main"

tasks:
  install:
    desc: Install Python dependencies (editable)
    cmds:
    - pip install -e .[dev]
  test:
    desc: Run pytest suite
    cmds:
    - pytest -q
  lint:
    desc: Run ruff lint check
    cmds:
    - ruff check .
  fmt:
    desc: Auto-format with ruff
    cmds:
    - ruff format .
  build:
    desc: Build wheel + sdist
    cmds:
    - python -m build
  clean:
    desc: Remove build artefacts
    cmds:
    - rm -rf build/ dist/ *.egg-info
  up:
    desc: Start services via docker compose
    cmds:
    - docker compose up -d
  down:
    desc: Stop services
    cmds:
    - docker compose down
  logs:
    desc: Tail compose logs
    cmds:
    - docker compose logs -f
  ps:
    desc: Show running compose services
    cmds:
    - docker compose ps
  docker-build:
    desc: Build docker image
    cmds:
    - docker build -t redsl:latest .
  help:
    desc: '[imported from Makefile] help'
    cmds:
    - "echo \"Dost\u0119pne komendy:\""
    - "echo \"  install       - Instalacja zale\u017Cno\u015Bci produkcyjnych\""
    - "echo \"  dev-install   - Instalacja zale\u017Cno\u015Bci deweloperskich\""
    - "echo \"  test          - Uruchomienie test\xF3w pytest (bez slow)\""
    - echo "  test-fast     - Szybkie testy (bez slow/integration/e2e)"
    - "echo \"  test-all      - Wszystkie testy w\u0142\u0105cznie z slow\""
    - echo "  lint          - Sprawdzenie lintingu ruff"
    - "echo \"  type-check    - Sprawdzenie typ\xF3w mypy\""
    - echo "  format        - Formatowanie kodu ruff"
    - echo "  format-check  - Sprawdzenie formatowania kodu"
    - "echo \"  docker-up     - Uruchomienie us\u0142ug Docker\""
    - "echo \"  docker-down   - Zatrzymanie us\u0142ug Docker\""
    - "echo \"  docker-build  - Budowanie obraz\xF3w Docker\""
    - echo "  run           - Uruchomienie aplikacji w Docker"
    - echo "  run-local     - Uruchomienie aplikacji lokalnie"
    - "echo \"  clean         - Czyszczenie plik\xF3w tymczasowych\""
  dev-install:
    desc: '[imported from Makefile] dev-install'
    cmds:
    - $(PIP) install -r requirements.txt
    - $(PIP) install -e ".[dev]"
  test-fast:
    desc: '[imported from Makefile] test-fast'
    cmds:
    - $(PYTHON) -m pytest tests/ -q -m "not slow and not integration and not e2e"
  test-all:
    desc: '[imported from Makefile] test-all'
    cmds:
    - $(PYTHON) -m pytest tests/ -v
  type-check:
    desc: '[imported from Makefile] type-check'
    cmds:
    - $(PYTHON) -m mypy redsl/
  format:
    desc: '[imported from Makefile] format'
    cmds:
    - $(PYTHON) -m ruff format redsl/ tests/
    - $(PYTHON) -m ruff check --fix redsl/ tests/
  format-check:
    desc: '[imported from Makefile] format-check'
    cmds:
    - $(PYTHON) -m ruff format --check redsl/ tests/
  docker-up:
    desc: '[imported from Makefile] docker-up'
    cmds:
    - $(DOCKER_COMPOSE) up -d
  docker-down:
    desc: '[imported from Makefile] docker-down'
    cmds:
    - $(DOCKER_COMPOSE) down
  run:
    desc: '[imported from Makefile] run'
    deps:
    - docker-up
  run-local:
    desc: '[imported from Makefile] run-local'
    cmds:
    - $(PYTHON) -m uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000
  health:
    desc: '[from doql] workflow: health'
    cmds:
    - docker compose ps
    - docker compose exec app echo "Health check passed"
  import-makefile-hint:
    desc: '[from doql] workflow: import-makefile-hint'
    cmds:
    - 'echo ''Run: taskfile import Makefile to import existing targets.'''
  all:
    desc: Run install, lint, test
    cmds:
    - taskfile run install
    - taskfile run lint
    - taskfile run test
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
project_root: .
package_name: redsl
include:
- '**/*.py'
exclude:
- '**/__pycache__/**'
- '**/node_modules/**'
- '**/.venv/**'
- '**/venv/**'
- '**/.git/**'
- '**/build/**'
- '**/dist/**'
- '**/*.egg-info/**'
- '**/tests/**'
tools:
  parallel: true
  cache: true
  ruff:
    enabled: true
    max_line_length: 88
    select:
    - E
    - F
    - W
    - I
    - C
    - B
    - A
    - COM
    - C4
    - DTZ
    - T10
    - EM
    - EXE
    - FA
    - ISC
    - ICN
    - G
    - INP
    - PIE
    - T20
    - PT
    - Q
    - RSE
    - RET
    - SIM
    - TID
    - TCH
    - ARG
    - PTH
    - ERA
    - PGH
    - PL
    - TRY
    - FLAKE8-PYTESTSTYLE
    - RUF
    ignore:
    - E501
    - PLR0913
    - PLR0915
  mypy:
    enabled: true
    strict: false
    ignore_missing_imports: true
    disallow_untyped_defs: false
    disallow_incomplete_defs: false
    check_untyped_defs: true
    disallow_untyped_decorators: false
    no_implicit_optional: true
    warn_redundant_casts: true
    warn_unused_ignores: true
    warn_no_return: true
    warn_unreachable: true
    strict_equality: true
  isort:
    enabled: true
    profile: black
    multi_line_output: 3
    line_length: 88
  bandit:
    enabled: true
    exclude_dirs:
    - tests
  coverage:
    enabled: true
    fail_under: 80
  pydocstyle:
    enabled: true
    convention: google
  vulture:
    enabled: true
    min_confidence: 60
performance:
  max_workers: 4
  cache_size: 104857600
  chunk_size: 10
metrics:
  complexity:
    enabled: true
    max_complexity: 10
    tools:
    - radon
    - xenon
  maintainability:
    enabled: true
    min_maintainability: 70
    tools:
    - radon
  duplication:
    enabled: true
    min_similarity: 0.85
    tools:
    - jscpd
  test_coverage:
    enabled: true
    min_coverage: 80
    tools:
    - coverage
rules:
  unused-imports:
    enabled: true
    tools:
    - ruff
    - autoflake
    severity: error
  magic-numbers:
    enabled: true
    threshold: 2
    exclude:
    - 0
    - 1
    - -1
    - 2
    severity: warning
  print-statements:
    enabled: true
    severity: warning
  TODO-comments:
    enabled: true
    severity: info
  long-lines:
    enabled: true
    max_length: 88
    severity: warning
  missing-docstrings:
    enabled: true
    public_only: true
    severity: warning
  type-hints:
    enabled: true
    require_return_type: true
    require_param_types: false
    severity: warning
  security-issues:
    enabled: true
    tools:
    - bandit
    severity: error
  code-smells:
    enabled: true
    tools:
    - ruff
    - mypy
    severity: warning
plugins:
  enabled: true
  directories:
  - ~/.pyqual/plugins
  - ./.pyqual/plugins
environments:
  development:
    rules:
      print-statements:
        enabled: true
      magic-numbers:
        enabled: false
      TODO-comments:
        severity: warning
    performance:
      max_workers: 2
  production:
    rules:
      print-statements:
        enabled: false
      magic-numbers:
        enabled: true
      TODO-comments:
        severity: error
    performance:
      max_workers: 8
  testing:
    rules:
      print-statements:
        enabled: true
      magic-numbers:
        enabled: false
      missing-docstrings:
        enabled: false
    metrics:
      test_coverage:
        enabled: true
        min_coverage: 90
reporting:
  output_formats:
  - yaml
  - json
  - html
  include_summary: true
  include_details: true
  include_recommendations: true
  output_file: pyqual_report
```

## Configuration

```yaml
project:
  name: redsl
  version: 1.2.33
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
fastapi>=0.115.0
uvicorn>=0.44.0
pydantic>=2.10.0
litellm>=1.52.0
chromadb>=0.6.0
pyyaml>=6.0.2
rich>=13.9.0
httpx>=0.28.0
click>=8.1.7
python-dotenv>=1.0.1
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

### Development

```text markpact:deps python scope=dev
pytest>=9.0
pytest-xdist>=3.5
pytest-cov>=7.1
ruff>=0.15.0
mypy>=1.13
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Deployment

```bash markpact:run
pip install redsl

# development install
pip install -e .[dev]
```

### Requirements Files

#### `requirements.txt`

- `fastapi>=0.115.0`
- `uvicorn>=0.44.0`
- `pydantic>=2.10.0`
- `litellm>=1.52.0`
- `tiktoken>=0.8.0`
- `chromadb>=0.6.0`
- `pyyaml>=6.0.2`
- `ruff>=0.15.0`
- `typer>=0.12.0`
- `rich>=13.9.0`
- `aiofiles>=24.1.0`
- `httpx>=0.28.0`

### Docker

- **base image**: `python:3.12-slim`
- **entrypoint**: `["uvicorn", "redsl.api:app", "--host", "0.0.0.0", "--port", "8000"]`

### Docker Compose (`docker-compose.yml`)

- **agent** image=`.` ports: `8020:8000`
- **chroma** image=`chromadb/chroma:latest` ports: `8005:8000`
- **consciousness** image=`.`

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `sk-...` | === LLM === |
| `REFACTOR_LLM_MODEL` | `gpt-5.4-mini` |  |
| `REFACTOR_DRY_RUN` | `true` | === Refactor === |
| `REFACTOR_AUTO_APPROVE` | `false` |  |
| `PROJECT_PATH` | `./my-project` | === Project === |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`conscious-refactor-agent`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `redsl/__init__.py:__version__`

## Makefile Targets

- `PYTHON`
- `PIP`
- `DOCKER_COMPOSE`
- `help`
- `install`
- `dev-install`
- `test`
- `test-fast`
- `test-all`
- `lint`
- `type-check`
- `format`
- `format-check`
- `docker-up`
- `docker-down`
- `docker-build`
- `run`
- `run-local`
- `clean`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# redsl | 198f 26527L | shell:2,python:196 | 2026-04-19
# stats: 1122 func | 0 cls | 198 mod | CC̄=3.8 | critical:0 | cycles:0
# alerts[5]: fan-out run_memory_learning_example=32; fan-out _register_refactor_endpoints=21; fan-out main=19; fan-out run_audit_example=19; fan-out apply_quality_refactors=18
# hotspots[5]: run_memory_learning_example fan=32; _register_refactor_endpoints fan=21; main fan=19; run_audit_example fan=19; apply_quality_refactors fan=18
# evolution: CC̄ 3.8→3.8 (flat 0.0)
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[198]:
  .goal/pre-commit-hook.py,23
  .goal/vallm-pre-commit.sh,17
  app/models.py,48
  archive/legacy_scripts/apply_semcod_refactor.py,79
  archive/legacy_scripts/batch_quality_refactor.py,167
  archive/legacy_scripts/batch_refactor_semcod.py,154
  archive/legacy_scripts/debug_decisions.py,62
  archive/legacy_scripts/debug_llm_config.py,55
  archive/legacy_scripts/hybrid_llm_refactor.py,386
  archive/legacy_scripts/hybrid_quality_refactor.py,253
  examples/01-basic-analysis/main.py,26
  examples/02-custom-rules/main.py,27
  examples/03-full-pipeline/main.py,30
  examples/03-full-pipeline/refactor_output/refactor_extract_functions_20260407_145021/00_orders__service.py,88
  examples/04-memory-learning/main.py,29
  examples/05-api-integration/main.py,32
  examples/06-awareness/main.py,27
  examples/07-pyqual/main.py,27
  examples/08-audit/main.py,25
  examples/09-pr-bot/main.py,25
  examples/10-badge/main.py,25
  project.sh,35
  redsl/__init__.py,15
  redsl/__main__.py,6
  redsl/analyzers/__init__.py,64
  redsl/analyzers/analyzer.py,71
  redsl/analyzers/code2llm_bridge.py,178
  redsl/analyzers/incremental.py,291
  redsl/analyzers/metrics.py,81
  redsl/analyzers/parsers/__init__.py,29
  redsl/analyzers/parsers/duplication_parser.py,57
  redsl/analyzers/parsers/functions_parser.py,148
  redsl/analyzers/parsers/project_parser.py,300
  redsl/analyzers/parsers/validation_parser.py,40
  redsl/analyzers/python_analyzer.py,273
  redsl/analyzers/quality_visitor.py,209
  redsl/analyzers/radon_analyzer.py,388
  redsl/analyzers/redup_bridge.py,245
  redsl/analyzers/resolver.py,97
  redsl/analyzers/semantic_chunker.py,270
  redsl/analyzers/sumd_bridge.py,412
  redsl/analyzers/toon_analyzer.py,296
  redsl/analyzers/utils.py,140
  redsl/api/__init__.py,70
  redsl/api/debug_routes.py,56
  redsl/api/example_routes.py,95
  redsl/api/health_routes.py,20
  redsl/api/models.py,96
  redsl/api/pyqual_routes.py,33
  redsl/api/refactor_routes.py,291
  redsl/api/webhook_routes.py,16
  redsl/autonomy/__init__.py,38
  redsl/autonomy/adaptive_executor.py,106
  redsl/autonomy/auto_fix.py,220
  redsl/autonomy/growth_control.py,277
  redsl/autonomy/intent.py,167
  redsl/autonomy/metrics.py,249
  redsl/autonomy/quality_gate.py,325
  redsl/autonomy/review.py,143
  redsl/autonomy/scheduler.py,264
  redsl/autonomy/smart_scorer.py,122
  redsl/awareness/__init__.py,325
  redsl/awareness/change_patterns.py,125
  redsl/awareness/ecosystem.py,134
  redsl/awareness/git_timeline.py,165
  redsl/awareness/health_model.py,151
  redsl/awareness/proactive.py,138
  redsl/awareness/self_model.py,121
  redsl/awareness/timeline_analysis.py,169
  redsl/awareness/timeline_git.py,128
  redsl/awareness/timeline_models.py,107
  redsl/awareness/timeline_toon.py,173
  redsl/ci/__init__.py,15
  redsl/ci/github_actions.py,260
  redsl/cli/__init__.py,81
  redsl/cli/__main__.py,1
  redsl/cli/batch.py,116
  redsl/cli/debug.py,60
  redsl/cli/examples.py,118
  redsl/cli/logging.py,48
  redsl/cli/pyqual.py,35
  redsl/cli/refactor.py,293
  redsl/cli/scan.py,41
  redsl/cli/utils.py,45
  redsl/commands/_fixer_utils.py,13
  redsl/commands/_guard_fixers.py,179
  redsl/commands/_indent_fixers.py,188
  redsl/commands/_scan_report.py,158
  redsl/commands/autofix/__init__.py,28
  redsl/commands/autofix/discovery.py,26
  redsl/commands/autofix/helpers.py,17
  redsl/commands/autofix/hybrid.py,57
  redsl/commands/autofix/models.py,30
  redsl/commands/autofix/pipeline.py,126
  redsl/commands/autofix/reporting.py,138
  redsl/commands/autofix/runner.py,56
  redsl/commands/autofix/todo_gen.py,72
  redsl/commands/autonomy_pr/__init__.py,134
  redsl/commands/autonomy_pr/analyzer.py,155
  redsl/commands/autonomy_pr/git_ops.py,204
  redsl/commands/autonomy_pr/models.py,46
  redsl/commands/autonomy_pr/reporter.py,40
  redsl/commands/autonomy_pr/validator.py,314
  redsl/commands/batch.py,139
  redsl/commands/batch_pyqual/__init__.py,41
  redsl/commands/batch_pyqual/config_gen.py,81
  redsl/commands/batch_pyqual/discovery.py,66
  redsl/commands/batch_pyqual/models.py,62
  redsl/commands/batch_pyqual/pipeline.py,390
  redsl/commands/batch_pyqual/reporting.py,332
  redsl/commands/batch_pyqual/runner.py,170
  redsl/commands/batch_pyqual/utils.py,37
  redsl/commands/batch_pyqual/verdict.py,109
  redsl/commands/cli_autonomy.py,350
  redsl/commands/cli_awareness.py,83
  redsl/commands/cli_doctor.py,116
  redsl/commands/doctor.py,124
  redsl/commands/doctor_data.py,41
  redsl/commands/doctor_detectors.py,319
  redsl/commands/doctor_fixers.py,214
  redsl/commands/doctor_fstring_fixers.py,155
  redsl/commands/doctor_helpers.py,40
  redsl/commands/doctor_indent_fixers.py,31
  redsl/commands/hybrid.py,304
  redsl/commands/multi_project.py,251
  redsl/commands/planfile_bridge.py,201
  redsl/commands/pyqual/__init__.py,349
  redsl/commands/pyqual/ast_analyzer.py,88
  redsl/commands/pyqual/bandit_analyzer.py,47
  redsl/commands/pyqual/mypy_analyzer.py,61
  redsl/commands/pyqual/reporter.py,148
  redsl/commands/pyqual/ruff_analyzer.py,49
  redsl/commands/scan.py,213
  redsl/config.py,134
  redsl/consciousness_loop.py,204
  redsl/diagnostics/__init__.py,17
  redsl/diagnostics/perf_bridge.py,289
  redsl/dsl/__init__.py,22
  redsl/dsl/engine.py,290
  redsl/dsl/rule_generator.py,271
  redsl/examples/__init__.py,33
  redsl/examples/_common.py,94
  redsl/examples/api_integration.py,41
  redsl/examples/audit.py,157
  redsl/examples/awareness.py,101
  redsl/examples/badge.py,158
  redsl/examples/basic_analysis.py,54
  redsl/examples/custom_rules.py,68
  redsl/examples/full_pipeline.py,67
  redsl/examples/memory_learning.py,117
  redsl/examples/pr_bot.py,136
  redsl/examples/pyqual_example.py,74
  redsl/execution/__init__.py,87
  redsl/execution/cycle.py,172
  redsl/execution/decision.py,372
  redsl/execution/executor.py,74
  redsl/execution/reflector.py,106
  redsl/execution/reporter.py,86
  redsl/execution/resolution.py,154
  redsl/execution/sandbox_execution.py,69
  redsl/execution/validation.py,57
  redsl/formatters/__init__.py,65
  redsl/formatters/batch.py,212
  redsl/formatters/core.py,14
  redsl/formatters/cycle.py,233
  redsl/formatters/debug.py,36
  redsl/formatters/refactor.py,183
  redsl/history.py,210
  redsl/integrations/__init__.py,1
  redsl/integrations/webhook.py,109
  redsl/llm/__init__.py,213
  redsl/llm/llx_router.py,285
  redsl/main.py,272
  redsl/memory/__init__.py,235
  redsl/orchestrator.py,170
  redsl/refactors/__init__.py,55
  redsl/refactors/_base.py,15
  redsl/refactors/ast_transformers.py,131
  redsl/refactors/body_restorer.py,203
  redsl/refactors/diff_manager.py,283
  redsl/refactors/direct.py,63
  redsl/refactors/direct_constants.py,130
  redsl/refactors/direct_guard.py,130
  redsl/refactors/direct_imports.py,210
  redsl/refactors/direct_types.py,124
  redsl/refactors/engine.py,336
  redsl/refactors/models.py,49
  redsl/refactors/prompts.py,277
  redsl/utils/__init__.py,1
  redsl/utils/tool_check.py,21
  redsl/validation/__init__.py,30
  redsl/validation/pyqual_bridge.py,249
  redsl/validation/regix_bridge.py,317
  redsl/validation/sandbox.py,210
  redsl/validation/testql_bridge.py,297
  redsl/validation/vallm_bridge.py,314
  refactor_output/refactor_extract_functions_20260407_143102/00_app__models.py,29
  test_sample_project/sample.py,32
D:
  archive/legacy_scripts/batch_quality_refactor.py:
    e: apply_quality_refactors,main
    apply_quality_refactors(project_path)
    main()
  redsl/analyzers/toon_analyzer.py:
    e: ToonAnalyzer
    ToonAnalyzer: __init__(2),analyze_project(1),analyze_from_toon_content(3),_find_toon_files(1),_select_project_key(1),_process_project_ton(2),_convert_modules_to_metrics(2),_process_hotspots(2),_process_alerts(2),_process_duplicates(2),_process_validation(2),_resolve_and_filter_metrics(2),_calculate_statistics(1)  # Analizator plików toon — przetwarza dane z code2llm...
  redsl/commands/autonomy_pr/__init__.py:
    e: _step_finalize,run_autonomous_pr
    _step_finalize(clone_path;branch_name;real_changes;max_actions;use_gh;git_url;clone_url)
    run_autonomous_pr(git_url;max_actions;dry_run;auto_apply;target_file;work_dir;branch_name;fmt)
  archive/legacy_scripts/batch_refactor_semcod.py:
    e: apply_refactor,measure_todo_reduction,main
    apply_refactor(project_path;max_actions)
    measure_todo_reduction(project_path)
    main()
  redsl/commands/autofix/reporting.py:
    e: _aggregate_totals,_project_details,_build_summary,_print_summary,_save_reports
    _aggregate_totals(results)
    _project_details(results)
    _build_summary(results)
    _print_summary(summary;results)
    _save_reports(results;summary;semcod_root)
  redsl/commands/autonomy_pr/validator.py:
    e: _step_validate,_run_testql_validation,_run_quality_gate,_run_project_tests,_check_testql_available,_detect_api_base_url,_detect_test_command
    _step_validate(clone_path)
    _run_testql_validation(project_dir)
    _run_quality_gate(project_dir)
    _run_project_tests(project_dir)
    _check_testql_available()
    _detect_api_base_url(project_dir)
    _detect_test_command(project_dir)
  redsl/commands/batch_pyqual/reporting.py:
    e: _count_by_status,_count_passed,_count_failed,_count_ready,_count_skipped,_aggregate_metrics,_aggregate_verdicts,_aggregate_timing,_compute_batch_verdict,_build_totals,_build_gate_pipeline_totals,_build_git_totals,_build_pipeline_totals,_build_project_detail,_build_summary,_format_summary_verdicts,_format_summary_config_and_gates,_format_summary_pipeline_and_totals,_print_summary,_build_report_header,_format_project_row,_build_project_table,_build_project_notes,_build_report_footer,_save_report
    _count_by_status(results;verdict)
    _count_passed(results)
    _count_failed(results)
    _count_ready(results)
    _count_skipped(results)
    _aggregate_metrics(results)
    _aggregate_verdicts(results)
    _aggregate_timing(results)
    _compute_batch_verdict(results)
    _build_totals(results;metrics;verdicts)
    _build_gate_pipeline_totals(results)
    _build_git_totals(results)
    _build_pipeline_totals(results)
    _build_project_detail(r)
    _build_summary(results)
    _format_summary_verdicts(summary)
    _format_summary_config_and_gates(summary)
    _format_summary_pipeline_and_totals(summary)
    _print_summary(summary)
    _build_report_header(summary;workspace_root;now)
    _format_project_row(i;r)
    _build_project_table(results)
    _build_project_notes(results)
    _build_report_footer()
    _save_report(results;summary;workspace_root)
  redsl/refactors/engine.py:
    e: RefactorEngine
    RefactorEngine: __init__(2),estimate_confidence(0),_parse_confidence(0),_resolve_confidence(2),generate_proposal(3),reflect_on_proposal(3),validate_proposal(2),apply_proposal(2),_save_proposal(1)  # Silnik refaktoryzacji z pętlą refleksji.

1. Generuj propozy...
  redsl/awareness/change_patterns.py:
    e: ChangePattern,ChangePatternLearner
    ChangePattern: to_dict(0)  # A learned pattern describing a recurring change shape...
    ChangePatternLearner: __init__(0),learn_from_timeline(2),summarize_patterns(0),recall_by_signal(1),_estimate_effectiveness(2)  # Infer patterns from timeline deltas and trend transitions...
  redsl/validation/testql_bridge.py:
    e: TestqlVerdict,TestqlValidator,validate_with_testql,check_testql_available
    TestqlVerdict: skipped_result(1)  # Validation verdict from testql scenario execution...
    TestqlValidator: __init__(2),_check_testql(0),validate(1),_run_scenario(2),_detect_base_url(0),generate_smoke_scenarios(1),_write_smoke_scenarios(2)  # Post-refactoring validator using testql scenarios.

Runs tes...
    validate_with_testql(project_dir;scenarios_dir;config)
    check_testql_available()
  redsl/analyzers/parsers/project_parser.py:
    e: ProjectParser
    ProjectParser: parse_project_toon(1),_parse_header_lines(2),_detect_section_change(1),_parse_section_line(5),_parse_health_line(2),_parse_alerts_line(2),_parse_hotspots_line(2),_parse_modules_line(4),_parse_layers_section_line(3),_parse_refactors_line(2),_parse_header_line(1),_parse_emoji_alert_line(1),_parse_alert_line(1),_parse_hotspot_line(1),_parse_module_line(1),_parse_module_list_line(1),_parse_layers_line(1),_parse_refactor_line(1)  # Parser sekcji project_toon...
  redsl/analyzers/parsers/validation_parser.py:
    e: ValidationParser
    ValidationParser: parse_validation_toon(1)  # Parser sekcji validation_toon...
  redsl/analyzers/parsers/duplication_parser.py:
    e: DuplicationParser
    DuplicationParser: parse_duplication_toon(1)  # Parser sekcji duplication_toon...
  redsl/analyzers/python_analyzer.py:
    e: PythonAnalyzer,ast_max_nesting_depth,ast_cyclomatic_complexity
    PythonAnalyzer: analyze_python_files(1),_discover_python_files(1),_parse_single_file(2),_scan_top_nodes(3),_accumulate_file_metrics(2),add_quality_metrics(2)  # Analizator plików .py przez stdlib ast...
    ast_max_nesting_depth(node)
    ast_cyclomatic_complexity(node)
  redsl/commands/_guard_fixers.py:
    e: _fix_guard_in_try_block,_fix_guard_with_excess_indent,_process_guard_and_indent,_handle_guard,_collect_guard_body,_next_non_blank_index,_is_guard_followed_by_except
    _fix_guard_in_try_block(path)
    _fix_guard_with_excess_indent(path)
    _process_guard_and_indent(lines)
    _handle_guard(lines;i;new_lines)
    _collect_guard_body(lines;start)
    _next_non_blank_index(lines;start)
    _is_guard_followed_by_except(lines;start)
  redsl/history.py:
    e: HistoryEvent,HistoryWriter,HistoryReader,_default_history_dir
    HistoryEvent:  # A single persisted event in the refactor history...
    HistoryWriter: __init__(1),record(1),record_event(1),decision_signature(0),has_recent_signature(2)  # Append-only history logger backed by .redsl/history.jsonl...
    HistoryReader: __init__(1),load_events(0),filter_by_file(1),filter_by_type(1),has_recent_proposal(2),has_recent_ticket(1),generate_decision_report(0)  # Read-only access to .redsl/history.jsonl for querying and de...
    _default_history_dir(project_dir)
  redsl/commands/pyqual/__init__.py:
    e: PyQualAnalyzer,_format_pyqual_issues,_format_pyqual_metrics,_format_pyqual_recommendations,_print_pyqual_report,_get_output_dir,run_pyqual_analysis,run_pyqual_fix
    PyQualAnalyzer: __init__(1),_load_config(0),analyze_project(1),_find_python_files(1),_is_excluded(2),save_report(2)  # Python code quality analyzer — fasada nad wyspecjalizowanymi...
    _format_pyqual_issues(summary)
    _format_pyqual_metrics(metrics)
    _format_pyqual_recommendations(recommendations)
    _print_pyqual_report(project_name;results;output_file)
    _get_output_dir(project_path)
    run_pyqual_analysis(project_path;config_path;output_format)
    run_pyqual_fix(project_path;config_path)
  redsl/autonomy/quality_gate.py:
    e: GateVerdict,_collect_python_files,_file_cc_functions,_measure_metrics,_git_diff_names,_git_file_at_ref,_get_metrics_at_ref,_get_metrics_current,run_quality_gate,install_pre_commit_hook,_cli_main
    GateVerdict:  # Result of a quality gate check...
    _collect_python_files(project_dir)
    _file_cc_functions(path)
    _measure_metrics(project_dir;files)
    _git_diff_names(project_dir;ref)
    _git_file_at_ref(project_dir;rel_path;ref)
    _get_metrics_at_ref(project_dir;ref)
    _get_metrics_current(project_dir)
    run_quality_gate(project_dir)
    install_pre_commit_hook(project_dir)
    _cli_main()
  redsl/autonomy/growth_control.py:
    e: GrowthBudget,GrowthController,ModuleBudget,_should_skip,_python_files,_infer_module_type,check_module_budget
    GrowthBudget:  # LOC growth budget per iteration...
    GrowthController: __init__(1),check_growth(1),suggest_consolidation(1),_measure_weekly_growth(1),_find_untested_new_modules(1),_find_oversized_files(1),_find_tiny_modules(1),_group_by_prefix(1)  # Enforce growth budgets on a project...
    ModuleBudget:  # Complexity budget for a single module...
    _should_skip(path)
    _python_files(root)
    _infer_module_type(file_path)
    check_module_budget(file_path;module_type)
  redsl/refactors/body_restorer.py:
    e: _find_preceding_def,_body_after_def,_collect_guard_body,_unindent_4,_is_docstring_only,repair_file,repair_directory
    _find_preceding_def(lines;guard_idx)
    _body_after_def(lines;def_idx;guard_idx)
    _collect_guard_body(lines;guard_idx)
    _unindent_4(line)
    _is_docstring_only(body_lines)
    repair_file(path)
    repair_directory(root;dry_run)
  redsl/awareness/timeline_toon.py:
    e: ToonCollector
    ToonCollector: __init__(3),snapshot_for_commit(3),_collect_toon_contents(1),_empty_toon_contents(-1),_store_toon_content(3),_toon_bucket(1),_sorted_toon_candidates(1),_toon_candidate_priority(1),_is_duplication_file(0),_is_validation_file(0)  # Collects and processes toon files from git history...
  redsl/awareness/timeline_analysis.py:
    e: TimelineAnalyzer
    TimelineAnalyzer: analyze_trends(1),predict_future_state(1),find_degradation_sources(0),_build_series_map(0),_apply_trend_aliases(0),_linear_regression(0),_analyze_series(2)  # Analyzes metric trends from timeline data...
  redsl/validation/sandbox.py:
    e: DockerNotFoundError,SandboxError,RefactorSandbox,_docker_available,_pactfix_available,sandbox_available
    DockerNotFoundError(RuntimeError):  # Raised when Docker daemon is not available...
    SandboxError(RuntimeError):  # Raised for sandbox-level failures...
    RefactorSandbox: __init__(2),start(0),apply_and_test(1),stop(0),__enter__(0),__exit__(0)  # Docker sandbox do bezpiecznego testowania refaktoryzacji...
    _docker_available()
    _pactfix_available()
    sandbox_available()
  redsl/validation/pyqual_bridge.py:
    e: is_available,_run_pyqual,doctor,_parse_gate_lines,_stage_passed,check_gates,get_status,validate_config,init_config,run_pipeline,git_commit,git_push
    is_available()
    _run_pyqual(project_dir;args;timeout)
    doctor(project_dir)
    _parse_gate_lines(output)
    _stage_passed(output;stage_name)
    check_gates(project_dir)
    get_status(project_dir)
    validate_config(project_dir;fix)
    init_config(project_dir;profile)
    run_pipeline(project_dir;fix_config;dry_run)
    git_commit(project_dir;message;add_all;if_changed)
    git_push(project_dir;detect_protection;dry_run)
  redsl/analyzers/sumd_bridge.py:
    e: SumdMetrics,SumdAnalyzer,analyze_with_sumd,_parse_map_metrics
    SumdMetrics:  # Metrics extracted from sumd analysis...
    SumdAnalyzer: __init__(0),analyze(1),generate_map_toon(1),_collect_modules(1),_detect_language(1),_analyze_py_file(1),_extract_function_info(2),_extract_class_info(2),_calculate_cc(1),_identify_hotspots(1),_generate_alerts(2)  # Native project analyzer using sumd extractor patterns.

Pure...
    analyze_with_sumd(project_dir)
    _parse_map_metrics(map_content)
  redsl/analyzers/semantic_chunker.py:
    e: SemanticChunk,SemanticChunker
    SemanticChunk: to_llm_prompt(0)  # Wycięty semantyczny fragment kodu gotowy do wysłania do LLM...
    SemanticChunker: _locate_function_data(2),_gather_chunk_contexts(7),chunk_function(4),_parse_source(0),_build_chunk(6),chunk_file(2),_find_nodes(2),_extract_relevant_imports(2),_extract_class_context(1),_extract_neighbors(4)  # Buduje semantyczne chunki kodu dla LLM...
  redsl/commands/_scan_report.py:
    e: _group_results_by_tier,_render_executive_summary,_render_priority_tiers,_render_analysis_errors,_render_report_header,_tier_names,_build_recommendations,render_markdown
    _group_results_by_tier(results)
    _render_executive_summary(results)
    _render_priority_tiers(tiers)
    _render_analysis_errors(errors)
    _render_report_header(now;folder;results;ok;errors)
    _tier_names(results;limit)
    _build_recommendations(tiers)
    render_markdown(results;folder)
  redsl/commands/planfile_bridge.py:
    e: is_available,_build_ticket_cmd,_extract_ticket_id,create_ticket,list_tickets,report_refactor_results,_safe_json
    is_available()
    _build_ticket_cmd(title;description;priority;labels)
    _extract_ticket_id(output)
    create_ticket(project_dir;title;description;priority;labels)
    list_tickets(project_dir;status)
    report_refactor_results(project_dir;decisions_applied;files_modified;avg_cc_before;avg_cc_after)
    _safe_json(text)
  redsl/commands/doctor_fstring_fixers.py:
    e: _write_if_parses,_fix_single_line_fstring_line,_apply_single_line_fstring_fixes,_fix_multiline_fstring_chunk,_consume_open_fstring_brace,_consume_close_fstring_brace,_fix_broken_fstring,_fix_multiline_fstring_braces,_escape_fstring_body_braces,_is_fstring_expr
    _write_if_parses(path;src)
    _fix_single_line_fstring_line(line)
    _apply_single_line_fstring_fixes(src)
    _fix_multiline_fstring_chunk(src)
    _consume_open_fstring_brace(body;i;result)
    _consume_close_fstring_brace(body;i;result)
    _fix_broken_fstring(path)
    _fix_multiline_fstring_braces(src)
    _escape_fstring_body_braces(body)
    _is_fstring_expr(inner)
  redsl/commands/doctor_fixers.py:
    e: fix_broken_guards,fix_stolen_indent,fix_broken_fstrings,fix_stale_pycache,fix_missing_install,fix_module_level_exit,fix_version_mismatch,fix_pytest_collision
    fix_broken_guards(root;report)
    fix_stolen_indent(root;report)
    fix_broken_fstrings(root;report)
    fix_stale_pycache(root;report)
    fix_missing_install(root;report)
    fix_module_level_exit(root;report)
    fix_version_mismatch(root;report)
    fix_pytest_collision(root;report)
  redsl/commands/doctor_detectors.py:
    e: _should_skip,_python_files,_read_python_source,_has_main_guard,_next_non_blank_index,_stolen_indent_issue_for_header,detect_broken_guards,detect_stolen_indent,detect_broken_fstrings,detect_stale_pycache,detect_missing_install,detect_module_level_exit,detect_version_mismatch,detect_pytest_cli_collision,_guess_package_name,_is_sys_exit_call
    _should_skip(path)
    _python_files(root)
    _read_python_source(path)
    _has_main_guard(lines)
    _next_non_blank_index(lines;start;stop)
    _stolen_indent_issue_for_header(lines;idx;rel)
    detect_broken_guards(root)
    detect_stolen_indent(root)
    detect_broken_fstrings(root)
    detect_stale_pycache(root)
    detect_missing_install(root)
    detect_module_level_exit(root)
    detect_version_mismatch(root)
    detect_pytest_cli_collision(root)
    _guess_package_name(root)
    _is_sys_exit_call(func)
  redsl/commands/batch_pyqual/verdict.py:
    e: _check_analysis_passed,_check_gates_passed,_check_pipeline_requirement,_check_push_requirement,_check_publish_requirement,_combine_verdicts,compute_verdict
    _check_analysis_passed(result)
    _check_gates_passed(result)
    _check_pipeline_requirement(result;require_pipeline)
    _check_push_requirement(result;require_push)
    _check_publish_requirement(result;require_publish)
    _combine_verdicts(checks)
    compute_verdict(result;require_pipeline;require_push;require_publish)
  redsl/commands/pyqual/ruff_analyzer.py:
    e: RuffAnalyzer
    RuffAnalyzer: analyze(3)  # Uruchamia ruff i zbiera wyniki...
  archive/legacy_scripts/hybrid_quality_refactor.py:
    e: apply_all_quality_changes,_parse_args,_find_projects,_count_todo_issues,_regenerate_todo,_process_single_project,_calculate_summary_stats,_print_summary,_save_results,main
    apply_all_quality_changes(project_path;max_changes)
    _parse_args()
    _find_projects(semcod_root)
    _count_todo_issues(todo_file)
    _regenerate_todo(project)
    _process_single_project(project;max_changes)
    _calculate_summary_stats(all_results)
    _print_summary(stats;all_results)
    _save_results(all_results;semcod_root)
    main()
  archive/legacy_scripts/hybrid_llm_refactor.py:
    e: _build_config,_select_decisions,_group_decisions_by_file,_build_changes_by_type,_apply_decision,_process_decisions_for_file,apply_changes_with_llm_supervision,_parse_args,_find_projects,_count_todo_issues,_regenerate_todo,_process_single_project,_calculate_summary_stats,_print_summary,_save_results,main
    _build_config(enable_llm)
    _select_decisions(orchestrator;analysis;enable_llm;max_changes)
    _group_decisions_by_file(decisions)
    _build_changes_by_type()
    _apply_decision(orchestrator;decision;project_path;changes_by_type)
    _process_decisions_for_file(orchestrator;file_path;decisions;project_path;max_changes;total_applied;total_errors;changes_by_type)
    apply_changes_with_llm_supervision(project_path;max_changes;enable_llm;validate_direct_changes)
    _parse_args()
    _find_projects(semcod_root)
    _count_todo_issues(todo_file)
    _regenerate_todo(project)
    _process_single_project(project;max_changes;enable_llm;validate_direct)
    _calculate_summary_stats(all_results;enable_llm)
    _print_summary(stats;all_results;enable_llm)
    _save_results(all_results;semcod_root;enable_llm)
    main()
  redsl/commands/batch_pyqual/pipeline.py:
    e: ProjectContext,_init_project_context,_validate_config,_run_analysis_stage,_run_redsl_fix_stage,_process_gate_result,_run_gates_stage,_run_pipeline_stage,_run_preflight_check,_commit_changes,_push_changes,_print_git_status,_run_git_stage,_finalize_result,process_project
    ProjectContext:  # Mutable context passed through pipeline stages...
    _init_project_context(project;profile;publish;dry_run;skip_dirty;pyqual_available)
    _validate_config(ctx;fix_config)
    _run_analysis_stage(ctx)
    _run_redsl_fix_stage(ctx;max_fixes)
    _process_gate_result(gate_result;result)
    _run_gates_stage(ctx)
    _run_pipeline_stage(ctx;run_pipeline;publish;fix_config;dry_run)
    _run_preflight_check(ctx)
    _commit_changes(ctx;status_lines)
    _push_changes(ctx)
    _print_git_status(ctx)
    _run_git_stage(ctx;git_push;dry_run)
    _finalize_result(ctx;require_pipeline;require_push;require_publish)
    process_project(project;max_fixes;run_pipeline;git_push;profile;publish;fix_config;dry_run;skip_dirty;pyqual_available)
  redsl/awareness/ecosystem.py:
    e: ProjectNode,EcosystemGraph
    ProjectNode: to_dict(0)  # Single project node in the ecosystem graph...
    EcosystemGraph: build(0),summarize(0),project(1),impacted_projects(1),_build_node(1),_link_dependencies(0),_read_dependencies(1),_extract_dependency_tokens(0),_is_project_dir(0)  # Basic ecosystem graph for semcod-style project collections...
  redsl/awareness/__init__.py:
    e: AwarenessSnapshot,AwarenessManager
    AwarenessSnapshot: to_dict(0),to_context(0),to_prompt_context(0)  # Compact overview of the current awareness state for a projec...
    AwarenessManager: __init__(4),_memory_fingerprint(0),_git_head(1),_build_cache_key(3),build_snapshot(3),build_context(3),build_prompt_context(3),history(2),ecosystem(1),health(2),predict(3),self_assess(1),_summarize_snapshot(4)  # Facade that combines all awareness layers into one snapshot...
  redsl/validation/vallm_bridge.py:
    e: _extract_json,_validation_target_path,_stage_validation_context,_run_vallm_validation,is_available,validate_patch,validate_proposal,blend_confidence
    _extract_json(text)
    _validation_target_path(validation_root;file_path;project_dir)
    _stage_validation_context(validation_root;file_path;refactored_code;project_dir;copied_dirs)
    _run_vallm_validation(file_path)
    is_available()
    validate_patch(file_path;refactored_code;project_dir)
    validate_proposal(proposal;project_dir)
    blend_confidence(base_confidence;vallm_score)
  redsl/analyzers/radon_analyzer.py:
    e: is_radon_available,_normalize_radon_path,_flatten_radon_blocks,_radon_block_name,_radon_block_type,_radon_block_complexity,_is_reasonable_radon_complexity,_radon_module_line_count,_alert_signature,run_radon_cc,extract_max_cc_per_file,enhance_metrics_with_radon,_collect_existing_metrics,_collect_existing_alerts,_get_allowed_paths,_process_radon_results,_count_blocks,_process_block_alert,_update_function_metrics,_update_module_metrics,_recompute_file_stats,_recompute_cc_avg,_update_result_stats
    is_radon_available()
    _normalize_radon_path(path_value;project_dir)
    _flatten_radon_blocks(entries)
    _radon_block_name(entry)
    _radon_block_type(entry)
    _radon_block_complexity(entry)
    _is_reasonable_radon_complexity(cc)
    _radon_module_line_count(project_dir;normalized_path)
    _alert_signature(alert)
    run_radon_cc(project_dir;excludes)
    extract_max_cc_per_file(radon_results;project_dir)
    enhance_metrics_with_radon(metrics;project_dir)
    _collect_existing_metrics(metric_list)
    _collect_existing_alerts(result)
    _get_allowed_paths(existing_module_metrics;existing_function_metrics)
    _process_radon_results(radon_results;project_dir;metric_list;max_cc_by_file;existing_function_metrics;existing_module_metrics;allowed_paths;result;existing_alerts)
    _count_blocks(direct_blocks)
    _process_block_alert(name;cc;result;existing_alerts;alert_count)
    _update_function_metrics(all_blocks;normalized_path;module_lines;module_cc;is_init_file;existing_function_metrics;metric_list;result;existing_alerts;updated;added;alert_count)
    _update_module_metrics(normalized_path;module_lines;module_cc;function_count;class_count;existing_module_metrics;updated)
    _recompute_file_stats(result;metric_list)
    _recompute_cc_avg(metric_list)
    _update_result_stats(result;metric_list;updated;added;alert_count)
  redsl/dsl/engine.py:
    e: Operator,RefactorAction,Condition,Rule,Decision,DSLEngine
    Operator(str,Enum):
    RefactorAction(str,Enum):
    Condition: evaluate(1),__repr__(0)  # Pojedynczy warunek DSL...
    Rule: evaluate(1),score(1),_calculate_impact(1)  # Reguła DSL: warunki → akcja z priorytetem...
    Decision:  # Wynik ewaluacji reguł — decyzja co refaktoryzować...
    DSLEngine: __init__(0),_load_default_rules(0),add_rule(1),add_rules_from_yaml(1),evaluate(1),top_decisions(2),explain(1)  # Silnik ewaluacji reguł DSL.

Przyjmuje zbiór reguł i konteks...
  redsl/commands/hybrid.py:
    e: _count_todo_issues,_regenerate_todo,_calculate_summary_stats,_print_summary,_writable_path,_save_results,_save_markdown_report,_apply_quality_decisions,_setup_hybrid_orchestrator,_get_quality_decisions,run_hybrid_quality_refactor,_find_projects,_process_single_project,run_hybrid_batch
    _count_todo_issues(todo_file)
    _regenerate_todo(project)
    _calculate_summary_stats(all_results)
    _print_summary(stats;all_results)
    _writable_path(base;filename)
    _save_results(all_results;semcod_root)
    _save_markdown_report(all_results;semcod_root;stats)
    _apply_quality_decisions(orchestrator;quality_decisions;project_path;max_changes)
    _setup_hybrid_orchestrator()
    _get_quality_decisions(orchestrator;analyzer;project_path)
    run_hybrid_quality_refactor(project_path;max_changes)
    _find_projects(semcod_root)
    _process_single_project(project;max_changes)
    run_hybrid_batch(semcod_root;max_changes)
  redsl/commands/_indent_fixers.py:
    e: _scan_next_nonblank,_process_def_block,_fix_stolen_indent,_handle_function_indent,_fix_body_indent,_detect_excess_indent,_strip_excess_indent,_check_excess_indent,_iterative_fix
    _scan_next_nonblank(lines;start)
    _process_def_block(lines;i;new_lines;changed)
    _fix_stolen_indent(path)
    _handle_function_indent(lines;i;new_lines;changed)
    _fix_body_indent(lines;i;new_lines;def_indent;expected;changed)
    _detect_excess_indent(lines;i;expected;def_indent)
    _strip_excess_indent(lines;i;new_lines;def_indent;expected;scan;changed)
    _check_excess_indent(lines;i;new_lines;def_indent;expected;changed)
    _iterative_fix(path;original_src)
  redsl/commands/pyqual/bandit_analyzer.py:
    e: BanditAnalyzer
    BanditAnalyzer: analyze(3)  # Uruchamia bandit i zbiera wyniki bezpieczeństwa...
  redsl/autonomy/review.py:
    e: review_staged_changes,_get_diff,_llm_review,_static_review,_parse_changed_files_from_diff,_simple_cc
    review_staged_changes(project_dir;model_override;max_diff_chars)
    _get_diff(project_dir)
    _llm_review(llm;diff;model_override)
    _static_review(project_dir;diff)
    _parse_changed_files_from_diff(diff)
    _simple_cc(node)
  redsl/formatters/cycle.py:
    e: format_cycle_report_yaml,_cycle_report_header_lines,_analysis_summary_lines,_execution_summary_lines,_cycle_summary_lines,_cycle_top_decisions_lines,_cycle_execution_results_lines,_cycle_error_lines,format_cycle_report_markdown,format_plan_yaml,_serialize_result
    format_cycle_report_yaml(report;decisions;analysis)
    _cycle_report_header_lines(title;now;project_path;log_file;report;dry_run)
    _analysis_summary_lines(analysis)
    _execution_summary_lines(report;dry_run)
    _cycle_summary_lines(analysis;decision_list;report;dry_run)
    _cycle_top_decisions_lines(decision_list)
    _cycle_execution_results_lines(report)
    _cycle_error_lines(report)
    format_cycle_report_markdown(report;decisions;analysis;project_path;log_file;dry_run)
    format_plan_yaml(decisions;analysis)
    _serialize_result(result)
  redsl/examples/memory_learning.py:
    e: _build_in_memory_agent_memory,run_memory_learning_example,main
    _build_in_memory_agent_memory(persist_dir)
    run_memory_learning_example(scenario;source)
    main(argv)
  redsl/execution/resolution.py:
    e: _resolve_source_path,_resolve_target_function,_load_source_code,_consult_memory,_consult_memory_for_decisions,_remember_decision_result
    _resolve_source_path(orchestrator;decision;project_dir)
    _resolve_target_function(orchestrator;source_path;decision)
    _load_source_code(orchestrator;source_path;decision)
    _consult_memory(orchestrator;decision)
    _consult_memory_for_decisions(orchestrator;decisions)
    _remember_decision_result(orchestrator;decision;proposal;result)
  redsl/execution/reporter.py:
    e: _resolve_source_preview,explain_decisions,get_memory_stats,estimate_cycle_cost
    _resolve_source_preview(orchestrator;project_dir;d)
    explain_decisions(orchestrator;project_dir;limit)
    get_memory_stats(orchestrator)
    estimate_cycle_cost(orchestrator;project_dir;max_actions)
  redsl/llm/llx_router.py:
    e: ModelSelection,_get_refactor_action_enum,_build_action_model_mapping,_build_model_matrix,_normalize_model_name,_model_family,_classify_complexity,_estimate_tokens,_estimate_cost,_ollama_available,_llx_available,select_model,select_reflection_model,estimate_cycle_cost,apply_provider_prefix,call_via_llx
    ModelSelection:
    _get_refactor_action_enum()
    _build_action_model_mapping(action_value;critical;high;any_model)
    _build_model_matrix()
    _normalize_model_name(model)
    _model_family(model)
    _classify_complexity(context)
    _estimate_tokens(context)
    _estimate_cost(model;tokens)
    _ollama_available(model)
    _llx_available()
    select_model(action;context;budget_remaining)
    select_reflection_model(use_local)
    estimate_cycle_cost(decisions;contexts)
    apply_provider_prefix(model;configured_model)
    call_via_llx(messages;task_type)
  redsl/refactors/prompts.py:
    e: _format_trends,_format_alerts,build_ecosystem_context
    _format_trends(trends)
    _format_alerts(alerts)
    build_ecosystem_context(context)
  redsl/refactors/direct_constants.py:
    e: DirectConstantsRefactorer
    DirectConstantsRefactorer(DirectRefactorBase): __init__(0),_build_value_to_names_map(2),_find_import_end_line(0),_replace_magic_numbers(4),extract_constants(2),_generate_constant_name(2)  # Handles magic number to constant extraction...
  redsl/refactors/diff_manager.py:
    e: generate_diff,preview_proposal,create_checkpoint,rollback_to_checkpoint,rollback_single_file,_is_git_repo,_rollback_git_stash,_rollback_files,_git_checkout_file
    generate_diff(original;refactored;file_path)
    preview_proposal(proposal;project_dir)
    create_checkpoint(project_dir)
    rollback_to_checkpoint(checkpoint_id;project_dir)
    rollback_single_file(file_path;checkpoint_id;project_dir)
    _is_git_repo(project_dir)
    _rollback_git_stash(stash_name;project_dir)
    _rollback_files(cp_name;project_dir)
    _git_checkout_file(rel_path;project_dir)
  redsl/awareness/health_model.py:
    e: HealthDimension,UnifiedHealth,HealthModel
    HealthDimension: to_dict(0)  # Single health dimension with score and rationale...
    UnifiedHealth: to_dict(0)  # Aggregated health snapshot...
    HealthModel: assess(2),_bounded_score(0),_status_for_score(0),_recommendations(1)  # Combine timeline metrics into a single health snapshot...
  redsl/validation/regix_bridge.py:
    e: is_available,snapshot,compare,compare_snapshots,check_gates,rollback_working_tree,validate_no_regression,validate_working_tree
    is_available()
    snapshot(project_dir;ref;timeout)
    compare(project_dir;before_ref;after_ref)
    compare_snapshots(project_dir;before;after)
    check_gates(project_dir)
    rollback_working_tree(project_dir)
    validate_no_regression(project_dir;rollback_on_failure)
    validate_working_tree(project_dir;before_snapshot;rollback_on_failure)
  redsl/analyzers/redup_bridge.py:
    e: is_available,scan_duplicates,scan_as_toon,_build_dup_index,enrich_analysis,get_refactor_suggestions,_extract_json,_strip_progress_output
    is_available()
    scan_duplicates(project_dir;min_lines;min_similarity)
    scan_as_toon(project_dir;min_lines;min_similarity)
    _build_dup_index(groups)
    enrich_analysis(analysis;project_dir)
    get_refactor_suggestions(project_dir)
    _extract_json(text)
    _strip_progress_output(text)
  redsl/analyzers/parsers/functions_parser.py:
    e: FunctionsParser
    FunctionsParser: parse_functions_toon(1),_handle_modules_line(4),_handle_function_details_line(5),_update_module_max_cc(3),_maybe_add_alert(2),_parse_function_csv_line(3)  # Parser sekcji functions_toon — per-funkcja CC...
  redsl/autonomy/scheduler.py:
    e: AutonomyMode,Scheduler
    AutonomyMode(str,Enum):
    Scheduler: __init__(4),run(0),stop(0),run_once(0),_has_changes_since_last_check(0),_git_head(0),_analyze(0),_check_trends(0),_check_proactive(0),_generate_proposals(1),_save_proposals(1),_apply_safe(1),_create_pr(1),_report_findings(3),_summary(1),_self_assess(0)  # Periodic quality-improvement loop...
  redsl/commands/doctor.py:
    e: diagnose,heal,heal_batch
    diagnose(root)
    heal(root;dry_run)
    heal_batch(semcod_root;dry_run)
  archive/legacy_scripts/apply_semcod_refactor.py:
    e: main
    main()
  redsl/commands/cli_doctor.py:
    e: _echo_json,_format_check_report,_format_heal_report,_format_batch_report,_register_doctor_check,_register_doctor_heal,_register_doctor_batch,register
    _echo_json(payload)
    _format_check_report(project_path;report)
    _format_heal_report(project_path;report)
    _format_batch_report(reports)
    _register_doctor_check(doctor_grp)
    _register_doctor_heal(doctor_grp)
    _register_doctor_batch(doctor_grp)
    register(cli)
  redsl/commands/batch_pyqual/runner.py:
    e: _pyqual_cli_available,_print_batch_header,_status_config_parts,_status_gates_parts,_status_git_parts,_format_project_status,run_pyqual_batch
    _pyqual_cli_available()
    _print_batch_header(workspace_root;project_count;pyqual_ok;pipeline_mode;git_push;publish;fix_config;dry_run;skip_dirty;profile)
    _status_config_parts(result)
    _status_gates_parts(result)
    _status_git_parts(result)
    _format_project_status(result)
    run_pyqual_batch(workspace_root;max_fixes;run_pipeline;git_push;limit;profile;publish;fix_config;include;exclude;dry_run;skip_dirty;fail_fast)
  redsl/commands/autofix/todo_gen.py:
    e: _count_todo_issues,_append_gate_violations_to_todo,_generate_todo_md
    _count_todo_issues(todo_file)
    _append_gate_violations_to_todo(todo_file;violations)
    _generate_todo_md(project;metrics;gate_violations)
  redsl/commands/pyqual/reporter.py:
    e: Reporter
    Reporter: calculate_metrics(3),_store_metrics_results(5),_collect_file_metrics(5),generate_recommendations(1),save_report(2)  # Generuje rekomendacje i zapisuje raporty analizy jakości...
  redsl/commands/autonomy_pr/analyzer.py:
    e: _parse_worktree_changes,_split_generated_and_real_changes,_refactor_cmd,_step_analyze,_run_auto_apply,_step_apply
    _parse_worktree_changes(status_output)
    _split_generated_and_real_changes(paths)
    _refactor_cmd(clone_path;max_actions;target_file;dry_run)
    _step_analyze(clone_path;max_actions;target_file)
    _run_auto_apply(clone_path;max_actions;target_file)
    _step_apply(clone_path;max_actions;target_file;auto_apply)
  redsl/autonomy/intent.py:
    e: analyze_commit_intent,_score_from_messages,_score_from_files,_select_primary_and_active,_recent_commit_messages,_changed_python_files,_assess_risk
    analyze_commit_intent(project_dir)
    _score_from_messages(commit_msgs;scores)
    _score_from_files(changed_files;scores)
    _select_primary_and_active(scores)
    _recent_commit_messages(project_dir;n)
    _changed_python_files(project_dir)
    _assess_risk(changed_files;intent)
  redsl/commands/scan.py:
    e: ProjectScanResult,_count_python_files,_detect_languages,_git_activity,_extract_hotspots,_compute_priority,_analyze_single_project,_is_project_dir,scan_folder
    ProjectScanResult: is_ok(0)  # Scan result for a single project...
    _count_python_files(project_path)
    _detect_languages(project_path)
    _git_activity(project_path;days)
    _extract_hotspots(result;top_n)
    _compute_priority(result)
    _analyze_single_project(project_path;analyzer)
    _is_project_dir(path)
    scan_folder(folder;progress)
  redsl/examples/pyqual_example.py:
    e: run_pyqual_example,main
    run_pyqual_example(scenario;source)
    main(argv)
  redsl/execution/decision.py:
    e: _select_decisions,_decision_matches_target,_execute_direct_refactor,_check_time_window_duplicate,_check_signature_duplicate,_generate_proposal_with_reflection,_apply_and_record_result,_execute_decision,_execute_decisions
    _select_decisions(orchestrator;analysis;max_actions;target_file)
    _decision_matches_target(decision;target_norm)
    _execute_direct_refactor(orchestrator;decision;project_dir)
    _check_time_window_duplicate(orchestrator;decision;project_dir)
    _check_signature_duplicate(orchestrator;decision)
    _generate_proposal_with_reflection(orchestrator;decision;source_code;signature)
    _apply_and_record_result(orchestrator;decision;proposal;project_dir)
    _execute_decision(orchestrator;decision;project_dir)
    _execute_decisions(orchestrator;decisions;project_dir;use_sandbox;report)
  redsl/refactors/direct_guard.py:
    e: DirectGuardRefactorer
    DirectGuardRefactorer(DirectRefactorBase): __init__(0),_is_main_guard_node(0),_collect_guarded_lines(1),_collect_module_execution_lines(2),_insert_main_guard(2),fix_module_execution_block(1)  # Handles main guard wrapping for module-level execution code...
  redsl/refactors/direct_types.py:
    e: DirectTypesRefactorer
    DirectTypesRefactorer(DirectRefactorBase): __init__(0),_collect_return_type_replacements(3),_find_signature_colon(2),add_return_types(2),_find_def_colon(1)  # Handles return type annotation addition...
  redsl/awareness/timeline_git.py:
    e: GitTimelineProvider
    GitTimelineProvider: __init__(2),_resolve_repo_root(0),_project_rel_path(0),_git_log(1),_git_show(2),_is_duplication_file(0),_is_validation_file(0)  # Provides git-based timeline data...
  redsl/memory/__init__.py:
    e: MemoryEntry,MemoryLayer,InMemoryCollection,AgentMemory
    MemoryEntry:  # Pojedynczy wpis w pamięci...
    MemoryLayer: __init__(2),_get_collection(0),store(1),recall(2),count(0),clear(0)  # Warstwa pamięci oparta na ChromaDB...
    InMemoryCollection: __init__(1),add(3),query(2),count(0)  # Fallback gdy ChromaDB nie jest dostępne...
    AgentMemory: __init__(1),remember_action(5),recall_similar_actions(2),learn_pattern(3),recall_patterns(2),store_strategy(3),recall_strategies(2),stats(0)  # Kompletny system pamięci z trzema warstwami.

- episodic: „c...
  redsl/analyzers/incremental.py:
    e: EvolutionaryCache,IncrementalAnalyzer,get_changed_files,get_staged_files,_file_hash
    EvolutionaryCache: __init__(1),_load(0),save(0),get(1),set(2),invalidate(1),clear(0)  # Cache wyników analizy per-plik oparty o hash pliku.

Pozwala...
    IncrementalAnalyzer: __init__(1),analyze_changed(3),_analyze_subset(2),_collect_cached_metrics(3),_calculate_result_stats(0),_merge_with_cache(3),_populate_cache(2)  # Analizuje tylko zmienione pliki i scala z cached wynikami.

...
    get_changed_files(project_dir;since)
    get_staged_files(project_dir)
    _file_hash(file_path)
  redsl/analyzers/resolver.py:
    e: PathResolver
    PathResolver: resolve_file_path(2),extract_function_source(1),find_worst_function(1),resolve_metrics_paths(2)  # Resolver ścieżek i kodu źródłowego funkcji...
  redsl/autonomy/auto_fix.py:
    e: AutoFixResult,auto_fix_violations,_extract_file_path,_extract_function_name,_attempt_fix,_match_violation_handler,_handle_oversized_file,_handle_high_cc_function,_auto_split_module,_auto_extract_functions,_auto_reduce_cc_mean,_auto_fix_criticals,_create_fix_ticket,_suggest_manual_action
    AutoFixResult:  # Outcome of the auto-fix pipeline...
    auto_fix_violations(project_dir;violations)
    _extract_file_path(violation)
    _extract_function_name(violation)
    _attempt_fix(project_dir;violation)
    _match_violation_handler(violation)
    _handle_oversized_file(project_dir;violation)
    _handle_high_cc_function(project_dir;violation)
    _auto_split_module(project_dir;file_path)
    _auto_extract_functions(project_dir;file_path;func_name)
    _auto_reduce_cc_mean(project_dir)
    _auto_fix_criticals(project_dir)
    _create_fix_ticket(project_dir;violation;reason)
    _suggest_manual_action(violation)
  redsl/analyzers/quality_visitor.py:
    e: CodeQualityVisitor
    CodeQualityVisitor(ast.NodeVisitor): __init__(0),visit_Import(1),visit_ImportFrom(1),visit_Name(1),visit_Assign(1),visit_Attribute(1),_get_root_name(1),visit_Constant(1),_count_untyped_params(1),visit_FunctionDef(1),visit_AsyncFunctionDef(1),visit_If(1),_is_main_guard(1),generic_visit(1),_is_import_used(1),get_unused_imports(0),has_module_execution_block(0),get_metrics(0)  # Detects common code quality issues in Python AST...
  redsl/refactors/ast_transformers.py:
    e: ReturnTypeAdder,UnusedImportRemover
    ReturnTypeAdder(ast.NodeTransformer): __init__(1),visit_FunctionDef(1),visit_AsyncFunctionDef(1),_get_type_from_constant(1),_infer_return_type(1),_extract_type_name(1)  # AST transformer to add return type annotations...
    UnusedImportRemover(ast.NodeTransformer): __init__(1),visit_Import(1),visit_ImportFrom(1)  # AST transformer to remove unused imports...
  redsl/orchestrator.py:
    e: CycleReport,RefactorOrchestrator
    CycleReport:  # Raport z jednego cyklu refaktoryzacji...
    RefactorOrchestrator: __init__(1),run_cycle(7),run_from_toon_content(5),add_custom_rules(1),_resolve_limits(1)  # Główny orkiestrator — „mózg" systemu.

Łączy:
- CodeAnalyzer...
  archive/legacy_scripts/debug_decisions.py:
    e: debug_decisions
    debug_decisions(project_path)
  redsl/commands/batch_pyqual/discovery.py:
    e: _is_package,_find_packages,_normalize_patterns,_matches_any,_filter_packages
    _is_package(path)
    _find_packages(workspace_root)
    _normalize_patterns(values)
    _matches_any(name;patterns)
    _filter_packages(packages;include;exclude)
  redsl/commands/autofix/hybrid.py:
    e: _run_hybrid_fix
    _run_hybrid_fix(project;max_changes)
  redsl/commands/pyqual/mypy_analyzer.py:
    e: MypyAnalyzer
    MypyAnalyzer: analyze(3),_parse_mypy_line(0)  # Uruchamia mypy i zbiera wyniki...
  redsl/commands/pyqual/ast_analyzer.py:
    e: AstAnalyzer
    AstAnalyzer: analyze(3),_analyze_file(6)  # Analizuje pliki Python przez AST w poszukiwaniu typowych pro...
  redsl/autonomy/adaptive_executor.py:
    e: AdaptiveExecutor
    AdaptiveExecutor: __init__(1),execute_adaptive(3),_adapt_strategy(2)  # Execute decisions while adapting strategy on repeated failur...
  redsl/examples/pr_bot.py:
    e: _delta,_print_risk_flags,_print_suggestions,_print_status_check,run_pr_bot_example,main
    _delta(before;after;lower_is_better)
    _print_risk_flags(flags)
    _print_suggestions(suggestions)
    _print_status_check(status)
    run_pr_bot_example(scenario;source)
    main(argv)
  redsl/autonomy/smart_scorer.py:
    e: smart_score,_trend_multiplier,_ecosystem_multiplier,_coupling_multiplier,_confidence_multiplier
    smart_score(rule;context)
    _trend_multiplier(context;timeline)
    _ecosystem_multiplier(context;ecosystem)
    _coupling_multiplier(context;coupling)
    _confidence_multiplier(context;rule;self_model)
  redsl/formatters/refactor.py:
    e: format_refactor_plan,_format_yaml,_format_json,_build_decisions_table,_format_decision_details,_format_text,_serialize_analysis,_serialize_decision,_count_decision_types
    format_refactor_plan(decisions;format;analysis)
    _format_yaml(decisions;analysis)
    _format_json(decisions;analysis)
    _build_decisions_table(decisions)
    _format_decision_details(decisions)
    _format_text(decisions;analysis)
    _serialize_analysis(analysis)
    _serialize_decision(decision)
    _count_decision_types(decisions)
  redsl/autonomy/metrics.py:
    e: AutonomyMetrics,_check_gate_installed,_count_gate_blocks_last_week,_get_last_autonomous_pr,_count_self_refactors_last_month,_check_scheduler_running,_get_growth_last_week,collect_autonomy_metrics,save_metrics,load_metrics
    AutonomyMetrics: to_dict(0),to_json(0)  # Metrics for the autonomy subsystem...
    _check_gate_installed(project_dir)
    _count_gate_blocks_last_week(project_dir)
    _get_last_autonomous_pr(project_dir)
    _count_self_refactors_last_month(project_dir)
    _check_scheduler_running()
    _get_growth_last_week(project_dir)
    collect_autonomy_metrics(project_dir)
    save_metrics(metrics;path)
    load_metrics(path)
  redsl/formatters/batch.py:
    e: format_batch_results,_as_int,_batch_detail_name,_sum_metric,_batch_report_totals,_batch_header_lines,_batch_summary_lines,_batch_project_lines,_improvement_score,_batch_top_improvement_lines,_batch_error_lines,format_batch_report_markdown
    format_batch_results(results;format)
    _as_int(value;fallback)
    _batch_detail_name(detail)
    _sum_metric(details)
    _batch_report_totals(report;details)
    _batch_header_lines(title;now;root;projects_processed;total_decisions;total_applied;total_errors)
    _batch_summary_lines(total_before;total_after;total_decisions;total_applied;total_errors)
    _batch_project_lines(details)
    _improvement_score(item)
    _batch_top_improvement_lines(details)
    _batch_error_lines(details)
    format_batch_report_markdown(report;root;title)
  redsl/llm/__init__.py:
    e: LLMResponse,LLMLayer
    LLMResponse:  # Odpowiedź z modelu LLM...
    LLMLayer: __init__(1),_load_provider_key(3),_resolve_provider_key(2),_build_completion_kwargs(6),call(5),call_json(2),reflect(3)  # Warstwa abstrakcji nad LLM z obsługą:
- wywołań tekstowych
-...
  redsl/refactors/direct_imports.py:
    e: DirectImportRefactorer
    DirectImportRefactorer(DirectRefactorBase): __init__(0),remove_unused_imports(2),_collect_unused_import_edits(3),_collect_import_edits(5),_collect_import_from_edits(5),_is_star_import(0),_build_import_from_replacement(3),_alias_name(0),_format_alias(0),_remove_statement_lines(1),_remove_replaced_statement_lines(1),_apply_line_edits(3),_get_indent(0),_clean_blank_lines(0)  # Handles import-related direct refactoring...
  redsl/awareness/proactive.py:
    e: ProactiveAlert,ProactiveAnalyzer
    ProactiveAlert: to_dict(0)  # A proactive issue detected from trends...
    ProactiveAnalyzer: __init__(1),analyze(3),predict_future_state(3),_trend_alert(3)  # Turn trend forecasts into alerts and suggested interventions...
  redsl/analyzers/utils.py:
    e: _load_gitignore_patterns,_should_ignore_file,_matches_default_patterns,_is_gitignore_glob_pattern,_matches_gitignore_directory_pattern,_matches_gitignore_glob_pattern,_matches_gitignore_literal_pattern,_matches_gitignore_patterns,_try_number
    _load_gitignore_patterns(project_dir)
    _should_ignore_file(file_path;project_dir;gitignore_patterns)
    _matches_default_patterns(file_path)
    _is_gitignore_glob_pattern(pattern)
    _matches_gitignore_directory_pattern(pattern;rel_path)
    _matches_gitignore_glob_pattern(pattern;rel_path;rel_str)
    _matches_gitignore_literal_pattern(pattern;rel_str)
    _matches_gitignore_patterns(file_path;project_dir;gitignore_patterns)
    _try_number(val)
  redsl/api/example_routes.py:
    e: _get_runner_map,_get_runner,_serialize_example_result,_register_example_routes
    _get_runner_map()
    _get_runner(name)
    _serialize_example_result(result)
    _register_example_routes(app)
  redsl/execution/cycle.py:
    e: _new_cycle_report,_analyze_project,_summarize_analysis,run_cycle,run_from_toon_content
    _new_cycle_report(orchestrator)
    _analyze_project(orchestrator;project_dir;use_code2llm)
    _summarize_analysis(analysis)
    run_cycle(orchestrator;project_dir;max_actions;use_code2llm;validate_regix;rollback_on_failure;use_sandbox;target_file)
    run_from_toon_content(orchestrator;project_toon;duplication_toon;validation_toon;source_files;max_actions)
  redsl/config.py:
    e: LLMConfig,MemoryConfig,AnalyzerConfig,RefactorConfig,AgentConfig,_default_llm_model,_resolve_provider_key
    LLMConfig: api_key(1),api_key(1)  # Konfiguracja warstwy LLM...
    MemoryConfig:  # Konfiguracja systemu pamięci...
    AnalyzerConfig:  # Konfiguracja analizatora kodu...
    RefactorConfig:  # Konfiguracja silnika refaktoryzacji...
    AgentConfig: from_env(0)  # Główna konfiguracja agenta...
    _default_llm_model()
    _resolve_provider_key(model)
  redsl/commands/cli_autonomy.py:
    e: _echo_json,_format_gate_details,_format_gate_fix_result,_register_gate_check,_register_gate_details,_register_gate_install_hook,_register_gate_fix,_register_gate_commands,_register_review_commands,_register_watch_cmd,_format_improve_result,_register_improve_cmd,_register_watch_commands,_format_autonomy_status,_format_growth_report,_register_growth_cmd,_register_autonomy_status_cmd,_register_growth_and_status_commands,_register_pr_commands,register
    _echo_json(payload)
    _format_gate_details(verdict)
    _format_gate_fix_result(verdict;result)
    _register_gate_check(gate_grp)
    _register_gate_details(gate_grp)
    _register_gate_install_hook(gate_grp)
    _register_gate_fix(gate_grp)
    _register_gate_commands(cli)
    _register_review_commands(cli;host_module)
    _register_watch_cmd(cli;host_module)
    _format_improve_result(result)
    _register_improve_cmd(cli;host_module)
    _register_watch_commands(cli;host_module)
    _format_autonomy_status(metrics)
    _format_growth_report(warnings;suggestions)
    _register_growth_cmd(cli)
    _register_autonomy_status_cmd(cli)
    _register_growth_and_status_commands(cli)
    _register_pr_commands(cli)
    register(cli;host_module)
  examples/03-full-pipeline/refactor_output/refactor_extract_functions_20260407_145021/00_orders__service.py:
    e: process_order,_validate_order_and_user,_is_order_terminal,_calculate_order_total,_process_physical_item,_finalize_order
    process_order(order;user;db;mailer;logger;inventory;pricing;tax;discount;shipping)
    _validate_order_and_user(order;user;logger)
    _is_order_terminal(order;logger)
    _calculate_order_total(items;user;inventory;pricing;tax;discount;logger)
    _process_physical_item(item;inventory;pricing;tax;discount;user;logger)
    _finalize_order(order;total;db;mailer;logger)
  redsl/commands/autofix/runner.py:
    e: _format_project_status,run_autofix_batch
    _format_project_status(result)
    run_autofix_batch(semcod_root;max_changes)
  redsl/commands/autofix/pipeline.py:
    e: _stage_collect_metrics,_stage_ensure_todo,_stage_apply_fixes,_stage_quality_gate_check,_stage_pyqual_gates,_process_project
    _stage_collect_metrics(project;result)
    _stage_ensure_todo(project;result;metrics)
    _stage_apply_fixes(project;result;max_changes)
    _stage_quality_gate_check(project;result;todo_file)
    _stage_pyqual_gates(project)
    _process_project(project;max_changes)
  redsl/examples/custom_rules.py:
    e: _build_python_rule,run_custom_rules_example,main
    _build_python_rule(rule_data)
    run_custom_rules_example(scenario;source)
    main(argv)
  redsl/commands/autonomy_pr/git_ops.py:
    e: _https_to_ssh,_gh_available,_resolve_branch_name,_step_clone,_step_branch_and_commit,_step_push,_step_create_pr
    _https_to_ssh(url)
    _gh_available()
    _resolve_branch_name(clone_path;branch_name)
    _step_clone(git_url;clone_url;work_dir)
    _step_branch_and_commit(clone_path;branch_name;real_changes;max_actions)
    _step_push(clone_path;resolved_branch_name;use_gh)
    _step_create_pr(clone_path;resolved_branch_name;use_gh;real_changes;max_actions;clone_url)
  redsl/examples/badge.py:
    e: _compute_project_score,_grade_for_score,_dimension_color,_format_dimension_badges,_print_badge_code,_print_summary,run_badge_example,main
    _compute_project_score(metrics;scoring)
    _grade_for_score(score;scale)
    _dimension_color(val;db)
    _format_dimension_badges(metrics;dim_badges)
    _print_badge_code(grade;color;styles)
    _print_summary(results;scale)
    run_badge_example(scenario;source)
    main(argv)
  redsl/examples/awareness.py:
    e: _build_timeline,_print_patterns,_print_signals,_print_summary_section,run_awareness_example,main
    _build_timeline(raw_points)
    _print_patterns(patterns;display)
    _print_signals(patterns;learner;display)
    _print_summary_section(learner;display)
    run_awareness_example(scenario;source)
    main(argv)
  redsl/examples/audit.py:
    e: _compute_score,_grade_for_score,run_audit_example,main
    _compute_score(metrics)
    _grade_for_score(score;thresholds)
    run_audit_example(scenario;source)
    main(argv)
  redsl/formatters/debug.py:
    e: format_debug_info
    format_debug_info(info;format)
  redsl/cli/scan.py:
    e: _print_scan_summary,scan
    _print_scan_summary(results;output_path)
    scan(ctx;folder;output_path;quiet)
  redsl/cli/refactor.py:
    e: _resolve_cli_export,refactor,_handle_dry_run,_execute_refactor_cycle,_build_refactor_config,_collect_refactor_analysis_and_decisions,_decision_matches_target,_emit_refactor_dry_run,_build_json_report_payload,_emit_refactor_live_output,_save_refactor_markdown_report,_prepare_refactor_application,register_refactor
    _resolve_cli_export(name;fallback)
    refactor(ctx;project_path;max_actions;dry_run;format;use_code2llm;validate_regix;rollback;sandbox;target_file)
    _handle_dry_run(format;decisions;analysis;project_path;log_file)
    _execute_refactor_cycle(orchestrator;project_path;max_actions;use_code2llm;validate_regix;rollback;sandbox;target_file;decisions;analysis;format;log_file)
    _build_refactor_config(dry_run;project_path)
    _collect_refactor_analysis_and_decisions(orchestrator;project_path;max_actions;target_file)
    _decision_matches_target(decision;target_norm)
    _emit_refactor_dry_run(format;decisions;analysis)
    _build_json_report_payload(report;decisions;analysis)
    _emit_refactor_live_output(report;decisions;analysis;format)
    _save_refactor_markdown_report(project_path;report;decisions;analysis;log_file;dry_run)
    _prepare_refactor_application(format;sandbox;decisions;analysis)
    register_refactor(cli)
  redsl/diagnostics/perf_bridge.py:
    e: Bottleneck,CriticalStep,PerformanceReport,_metrun_available,_parse_metrun_output,_render_profile_stats,_profile_fallback_target,_parse_profile_bottlenecks,_build_fallback_suggestions,_fallback_profile,profile_refactor_cycle,profile_llm_latency,profile_memory_operations,generate_optimization_report
    Bottleneck:
    CriticalStep:
    PerformanceReport:
    _metrun_available()
    _parse_metrun_output(stdout)
    _render_profile_stats(pr)
    _profile_fallback_target(project_dir)
    _parse_profile_bottlenecks(stats_output)
    _build_fallback_suggestions(bottlenecks)
    _fallback_profile(project_dir)
    profile_refactor_cycle(project_dir)
    profile_llm_latency()
    profile_memory_operations()
    generate_optimization_report(project_dir)
  redsl/execution/validation.py:
    e: _snapshot_regix_before,_validate_with_regix
    _snapshot_regix_before(project_dir;validate_regix)
    _validate_with_regix(project_dir;before_snapshot;rollback_on_failure;report)
  redsl/ci/github_actions.py:
    e: WorkflowConfig,generate_github_workflow,install_github_workflow,_build_workflow,_build_steps,_build_gate_script,_pr_comment_script
    WorkflowConfig:  # Konfiguracja generowanego workflow...
    generate_github_workflow(project_dir;config;output_path)
    install_github_workflow(project_dir;config;overwrite)
    _build_workflow(cfg)
    _build_steps(cfg)
    _build_gate_script(gates)
    _pr_comment_script()
  redsl/awareness/self_model.py:
    e: CapabilityStat,AgentCapabilityProfile,SelfModel
    CapabilityStat: to_dict(0)  # Track how well the agent performs a capability...
    AgentCapabilityProfile: to_dict(0)  # Structured self-assessment summary...
    SelfModel: __init__(1),record_outcome(4),assess(1),summarize(0),_overall_confidence(0)  # Introspective model backed by agent memory...
  redsl/dsl/rule_generator.py:
    e: LearnedRule,RuleGenerator,_derive_conditions,_find_nearest_threshold
    LearnedRule: to_yaml_dict(0)  # Reguła DSL wygenerowana z wzorców w pamięci...
    RuleGenerator: __init__(1),generate(2),generate_from_history(3),save(2),load_and_register(2),_extract_patterns(0),_history_to_patterns(0),_patterns_to_rules(2)  # Generuje nowe reguły DSL z historii refaktoryzacji w pamięci...
    _derive_conditions(action;observations)
    _find_nearest_threshold(value;thresholds)
  redsl/api/refactor_routes.py:
    e: _run_refactor_analysis,_format_refactor_result,_register_analysis_endpoints,_collect_modified_files,_clear_project_history,_register_refactor_endpoints,_register_batch_routes,_register_refactor_routes
    _run_refactor_analysis(req)
    _format_refactor_result(decisions;analysis;fmt)
    _register_analysis_endpoints(app;orchestrator)
    _collect_modified_files(project_path)
    _clear_project_history(project_path)
    _register_refactor_endpoints(app;orchestrator)
    _register_batch_routes(app)
    _register_refactor_routes(app;orchestrator)
  redsl/main.py:
    e: _get_orchestrator,_analysis_source_method,_analysis_function_metrics,_print_analysis_summary,_print_top_functions,_print_alerts,_print_duplicates,_print_analysis_plan,cmd_analyze,cmd_explain,_print_refactor_report,cmd_refactor,cmd_memory_stats,cmd_serve,_print_usage,_get_arg,_has_flag,_dispatch_analyze,_dispatch_explain,_dispatch_refactor,_dispatch_memory_stats,_dispatch_serve,main
    _get_orchestrator(model)
    _analysis_source_method(orch;path)
    _analysis_function_metrics(result)
    _print_analysis_summary(result;path;source_method)
    _print_top_functions(func_metrics)
    _print_alerts(result;func_metrics)
    _print_duplicates(result)
    _print_analysis_plan(result;path)
    cmd_analyze(project_dir)
    cmd_explain(project_dir)
    _print_refactor_report(report;orch)
    cmd_refactor(project_dir;dry_run;auto;max_actions;model)
    cmd_memory_stats()
    cmd_serve(port;host)
    _print_usage()
    _get_arg(args;name;default)
    _has_flag(args;name)
    _dispatch_analyze(args)
    _dispatch_explain(args)
    _dispatch_refactor(args)
    _dispatch_memory_stats(args)
    _dispatch_serve(args)
    main()
  redsl/cli/logging.py:
    e: setup_logging
    setup_logging(project_path;verbose)
  redsl/consciousness_loop.py:
    e: ConsciousnessLoop,main_loop
    ConsciousnessLoop: __init__(3),run(0),_inner_thought(1),_self_assessment(1),_profile_performance(1),stop(0)  # Ciągła pętla „świadomości" agenta.

Agent nie czeka na polec...
    main_loop()
  archive/legacy_scripts/debug_llm_config.py:
    e: debug_llm
    debug_llm()
  redsl/commands/doctor_helpers.py:
    e: _find_pip,_fix_via_git_revert
    _find_pip(root)
    _fix_via_git_revert(path;root)
  redsl/commands/autofix/discovery.py:
    e: _is_package,_find_packages
    _is_package(path)
    _find_packages(semcod_root)
  redsl/commands/multi_project.py:
    e: ProjectAnalysis,MultiProjectReport,MultiProjectRunner,run_multi_analysis
    ProjectAnalysis:  # Wyniki analizy pojedynczego projektu...
    MultiProjectReport: worst_projects(1),summary(0),to_dict(0)  # Zbiorczy raport z analizy wielu projektów...
    MultiProjectRunner: __init__(1),analyze(2),analyze_from_paths(2),run_cycles(3),rank_by_priority(2),_analyze_one(1)  # Uruchamia ReDSL na wielu projektach...
    run_multi_analysis(project_dirs;config)
  redsl/execution/reflector.py:
    e: _reflect_on_cycle,_auto_learn_rules
    _reflect_on_cycle(orchestrator;report)
    _auto_learn_rules(orchestrator;report)
  redsl/awareness/git_timeline.py:
    e: GitTimelineAnalyzer
    GitTimelineAnalyzer: __init__(3),build_timeline(1),analyze_trends(2),predict_future_state(2),find_degradation_sources(1),summarize(1),_resolve_repo_root(0),_project_rel_path(0),_git_log(1),_snapshot_for_commit(3),_collect_toon_contents(1),_empty_toon_contents(-1),_store_toon_content(3),_toon_bucket(1),_sorted_toon_candidates(1),_toon_candidate_priority(1),_git_show(2),_is_duplication_file(0),_is_validation_file(0),_build_series_map(0),_apply_trend_aliases(0),_linear_regression(0),_analyze_series(3)  # Build a historical metric timeline from git commits — facade...
  redsl/analyzers/code2llm_bridge.py:
    e: is_available,generate_toon_files,read_toon_contents,analyze_with_code2llm,maybe_analyze
    is_available()
    generate_toon_files(project_dir;output_dir;timeout)
    read_toon_contents(toon_dir)
    analyze_with_code2llm(project_dir;analyzer;output_dir;timeout)
    maybe_analyze(project_dir;analyzer;output_dir)
  test_sample_project/sample.py:
    e: calculate_area,process_items,format_data
    calculate_area(radius)
    process_items(items)
    format_data(data)
  redsl/commands/batch.py:
    e: _find_todo_projects,_print_project_results,_process_batch_project,run_semcod_batch,apply_refactor,measure_todo_reduction,_save_markdown_report
    _find_todo_projects(semcod_root)
    _print_project_results(report)
    _process_batch_project(project;max_actions;total_results)
    run_semcod_batch(semcod_root;max_actions)
    apply_refactor(project_path;max_actions)
    measure_todo_reduction(project_path)
    _save_markdown_report(all_results;semcod_root)
  redsl/commands/batch_pyqual/utils.py:
    e: run_cmd,git_status_lines,resolve_profile
    run_cmd(cmd;cwd;timeout)
    git_status_lines(project)
    resolve_profile(requested_profile;run_pipeline;publish)
  redsl/commands/batch_pyqual/config_gen.py:
    e: _pyqual_cli_available,_generate_pyqual_yaml,_detect_publish_configured
    _pyqual_cli_available()
    _generate_pyqual_yaml(project;profile;pyqual_available)
    _detect_publish_configured(pyqual_yaml)
  redsl/commands/autonomy_pr/reporter.py:
    e: _print_workflow_header,_print_workflow_complete,_abort_no_changes
    _print_workflow_header(git_url;clone_url;use_gh;max_actions;branch_name;target_file)
    _print_workflow_complete(git_url;resolved_branch_name;clone_url)
    _abort_no_changes(apply_result)
  redsl/examples/_common.py:
    e: _examples_root,_resolve_yaml_path,load_example_yaml,list_available_examples,print_banner,parse_scenario
    _examples_root()
    _resolve_yaml_path(example_name;scenario)
    load_example_yaml(example_name;scenario;source)
    list_available_examples()
    print_banner(title;width;char)
    parse_scenario(argv)
  redsl/cli/examples.py:
    e: _run_example,example,example_basic_analysis,example_custom_rules,example_full_pipeline,example_memory_learning,example_api_integration,example_awareness,example_pyqual,example_audit,example_pr_bot,example_badge,example_list,register_examples
    _run_example(module;fn)
    example()
    example_basic_analysis(scenario;source)
    example_custom_rules(scenario;source)
    example_full_pipeline(scenario;model;source)
    example_memory_learning(scenario;source)
    example_api_integration(scenario;source)
    example_awareness(scenario;source)
    example_pyqual(scenario;source)
    example_audit(scenario;source)
    example_pr_bot(scenario;source)
    example_badge(scenario;source)
    example_list()
    register_examples(cli)
  redsl/execution/sandbox_execution.py:
    e: execute_sandboxed
    execute_sandboxed(orchestrator;decision;project_dir)
  redsl/examples/full_pipeline.py:
    e: run_full_pipeline_example,main
    run_full_pipeline_example(scenario;source;model)
    main(argv)
  redsl/integrations/webhook.py:
    e: handle_push_webhook,_analyze_repo,_create_github_issue
    handle_push_webhook(payload)
    _analyze_repo(repo)
    _create_github_issue(repo;title;body)
  refactor_output/refactor_extract_functions_20260407_143102/00_app__models.py:
    e: main_function,process_data,validate_data,save_data,log_error
    main_function(param1;param2)
    process_data(param)
    validate_data(data)
    save_data(data;param)
    log_error(message)
  redsl/examples/basic_analysis.py:
    e: run_basic_analysis_example,main
    run_basic_analysis_example(scenario;source)
    main(argv)
  redsl/cli/utils.py:
    e: perf_command,cost_command
    perf_command(ctx;project_path)
    cost_command(ctx;project_path;max_actions)
  redsl/cli/debug.py:
    e: debug,debug_ast,debug_llm,debug_metrics,register_debug
    debug()
    debug_ast(project_path;file)
    debug_llm(prompt;model)
    debug_metrics(project_path)
    register_debug(cli)
  redsl/cli/batch.py:
    e: batch,batch_semcod,batch_hybrid,batch_autofix,batch_pyqual_run,register_batch
    batch()
    batch_semcod(semcod_root;max_actions;format)
    batch_hybrid(semcod_root;max_changes)
    batch_autofix(ctx;semcod_root;max_changes)
    batch_pyqual_run(ctx;workspace_root;max_fixes;limit;include;exclude;profile;pipeline;push;publish;fix_config;dry_run;skip_dirty;fail_fast)
    register_batch(cli)
  redsl/awareness/timeline_models.py:
    e: MetricPoint,TrendAnalysis,TimelineSummary
    MetricPoint: to_dict(0)  # Single timeline point captured from a git commit...
    TrendAnalysis: to_dict(0)  # Trend summary for a single metric series...
    TimelineSummary: to_dict(0)  # High-level summary of a git timeline...
  .goal/pre-commit-hook.py:
    e: main
    main()
  redsl/commands/_fixer_utils.py:
    e: _read_source
    _read_source(path)
  redsl/commands/doctor_data.py:
    e: Issue,DoctorReport
    Issue:  # A single detected issue...
    DoctorReport: summary_dict(0)  # Aggregated report for one project...
  redsl/examples/api_integration.py:
    e: run_api_integration_example,main
    run_api_integration_example(scenario;source)
    main(argv)
  redsl/utils/tool_check.py:
    e: is_tool_available
    is_tool_available(cmd;timeout)
  redsl/analyzers/metrics.py:
    e: CodeMetrics,AnalysisResult
    CodeMetrics: to_dsl_context(0)  # Metryki pojedynczej funkcji/modułu...
    AnalysisResult: to_dsl_contexts(0)  # Wynik analizy projektu...
  examples/04-memory-learning/main.py:
    e: main
    main()
  examples/10-badge/main.py:
    e: main
    main()
  examples/09-pr-bot/main.py:
    e: main
    main()
  examples/05-api-integration/main.py:
    e: main
    main()
  examples/07-pyqual/main.py:
    e: main
    main()
  redsl/commands/cli_awareness.py:
    e: _echo_json,_init_manager,_register_history_command,_register_ecosystem_command,_register_health_command,_register_predict_command,_register_self_assess_command,register
    _echo_json(payload)
    _init_manager(host_module;project_path;ctx)
    _register_history_command(cli;host_module)
    _register_ecosystem_command(cli;host_module)
    _register_health_command(cli;host_module)
    _register_predict_command(cli;host_module)
    _register_self_assess_command(cli;host_module)
    register(cli;host_module)
  examples/08-audit/main.py:
    e: main
    main()
  examples/02-custom-rules/main.py:
    e: main
    main()
  examples/06-awareness/main.py:
    e: main
    main()
  examples/01-basic-analysis/main.py:
    e: main
    main()
  redsl/commands/autofix/helpers.py:
    e: _collect_python_files,_measure_metrics
    _collect_python_files(project)
    _measure_metrics(project;py_files)
  examples/03-full-pipeline/main.py:
    e: main
    main()
  redsl/formatters/core.py:
    e: _get_timestamp
    _get_timestamp()
  redsl/cli/pyqual.py:
    e: pyqual,pyqual_analyze,pyqual_fix,register_pyqual
    pyqual()
    pyqual_analyze(project_path;config;format)
    pyqual_fix(project_path;config)
    register_pyqual(cli)
  redsl/cli/__init__.py:
    e: cli,_build_awareness_manager,_register_all
    cli(ctx;verbose)
    _build_awareness_manager()
    _register_all(cli_group)
  redsl/refactors/direct.py:
    e: DirectRefactorEngine
    DirectRefactorEngine: __init__(0),remove_unused_imports(2),fix_module_execution_block(1),extract_constants(2),add_return_types(2),get_applied_changes(0)  # Applies simple refactorings directly via AST manipulation.

...
  redsl/refactors/_base.py:
    e: DirectRefactorBase
    DirectRefactorBase: get_applied_changes(0)  # Mixin that provides ``get_applied_changes`` for Direct* refa...
  redsl/analyzers/analyzer.py:
    e: CodeAnalyzer
    CodeAnalyzer: __init__(0),analyze_project(1),analyze_from_toon_content(3),resolve_file_path(2),extract_function_source(1),find_worst_function(1),resolve_metrics_paths(2),_ast_cyclomatic_complexity(0)  # Główny analizator kodu — fasada.

Deleguje do ToonAnalyzer (...
  redsl/api/pyqual_routes.py:
    e: _register_pyqual_routes
    _register_pyqual_routes(app)
  redsl/api/health_routes.py:
    e: _register_health_route
    _register_health_route(app;orchestrator)
  redsl/api/__init__.py:
    e: _build_api_orchestrator,create_app
    _build_api_orchestrator()
    create_app()
  redsl/api/webhook_routes.py:
    e: _register_webhook_routes
    _register_webhook_routes(app)
  redsl/api/debug_routes.py:
    e: _register_debug_routes
    _register_debug_routes(app;orchestrator)
  project.sh:
  .goal/vallm-pre-commit.sh:
  redsl/__init__.py:
  redsl/__main__.py:
  redsl/commands/doctor_indent_fixers.py:
  redsl/commands/batch_pyqual/__init__.py:
  redsl/commands/autofix/__init__.py:
  redsl/commands/autofix/models.py:
    e: ProjectFixResult
    ProjectFixResult:  # Result of autofix processing for a single project...
  redsl/examples/__init__.py:
  redsl/commands/batch_pyqual/models.py:
    e: PyqualProjectResult
    PyqualProjectResult:  # Result of pyqual pipeline for a single project...
  redsl/diagnostics/__init__.py:
  redsl/autonomy/__init__.py:
  redsl/formatters/__init__.py:
  redsl/cli/__main__.py:
  redsl/execution/__init__.py:
  redsl/execution/executor.py:
  redsl/commands/autonomy_pr/models.py:
    e: _CloneResult,_AnalysisResult,_ApplyResult,_CommitResult,_PushResult,_ValidationResult
    _CloneResult:
    _AnalysisResult:
    _ApplyResult:
    _CommitResult:
    _PushResult:
    _ValidationResult:
  redsl/refactors/__init__.py:
  redsl/ci/__init__.py:
  redsl/validation/__init__.py:
  redsl/utils/__init__.py:
  redsl/analyzers/__init__.py:
  redsl/analyzers/parsers/__init__.py:
    e: ToonParser
    ToonParser(ProjectParser,DuplicationParser,ValidationParser,FunctionsParser):  # Parser plików toon — fasada nad wyspecjalizowanymi parserami...
  redsl/integrations/__init__.py:
  redsl/dsl/__init__.py:
  redsl/refactors/models.py:
    e: FileChange,RefactorProposal,RefactorResult
    FileChange:  # Zmiana w pojedynczym pliku...
    RefactorProposal:  # Propozycja refaktoryzacji wygenerowana przez LLM...
    RefactorResult:  # Wynik zastosowania refaktoryzacji...
  app/models.py:
    e: FileChange,RefactorProposal,RefactorResult
    FileChange:  # Zmiana w pojedynczym pliku...
    RefactorProposal:  # Propozycja refaktoryzacji wygenerowana przez LLM...
    RefactorResult:  # Wynik zastosowania refaktoryzacji...
  redsl/api/models.py:
    e: AnalyzeRequest,RefactorRequest,BatchSemcodRequest,BatchHybridRequest,DebugConfigRequest,DebugDecisionsRequest,PyQualAnalyzeRequest,PyQualFixRequest,RulesRequest,ExampleRunRequest,DecisionResponse,CycleRequest,CycleResponse
    AnalyzeRequest(BaseModel):
    RefactorRequest(BaseModel):
    BatchSemcodRequest(BaseModel):
    BatchHybridRequest(BaseModel):
    DebugConfigRequest(BaseModel):
    DebugDecisionsRequest(BaseModel):
    PyQualAnalyzeRequest(BaseModel):
    PyQualFixRequest(BaseModel):
    RulesRequest(BaseModel):
    ExampleRunRequest(BaseModel):
    DecisionResponse(BaseModel):
    CycleRequest(BaseModel):
    CycleResponse(BaseModel):
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `redsl.main` (`redsl/main.py`)

```python
def _get_orchestrator(model)  # CC=2, fan=2
def _analysis_source_method(orch, path)  # CC=2, fan=3
def _analysis_function_metrics(result)  # CC=4, fan=1
def _print_analysis_summary(result, path, source_method)  # CC=2, fan=1
def _print_top_functions(func_metrics)  # CC=5, fan=1
def _print_alerts(result, func_metrics)  # CC=6, fan=2
def _print_duplicates(result)  # CC=3, fan=3
def _print_analysis_plan(result, path)  # CC=5, fan=7
def cmd_analyze(project_dir)  # CC=2, fan=13
def cmd_explain(project_dir)  # CC=1, fan=4
def _print_refactor_report(report, orch)  # CC=3, fan=3
def cmd_refactor(project_dir, dry_run, auto, max_actions, model)  # CC=2, fan=5
def cmd_memory_stats()  # CC=1, fan=4
def cmd_serve(port, host)  # CC=1, fan=1
def _print_usage()  # CC=1, fan=1
def _get_arg(args, name, default)  # CC=4, fan=2
def _has_flag(args, name)  # CC=1, fan=0
def _dispatch_analyze(args)  # CC=1, fan=2
def _dispatch_explain(args)  # CC=1, fan=2
def _dispatch_refactor(args)  # CC=2, fan=4
def _dispatch_memory_stats(args)  # CC=1, fan=1
def _dispatch_serve(args)  # CC=1, fan=3
def main()  # CC=3, fan=6
```

### `redsl.history` (`redsl/history.py`)

```python
def _default_history_dir(project_dir)  # CC=1, fan=0
class HistoryEvent:  # A single persisted event in the refactor history.
class HistoryWriter:  # Append-only history logger backed by .redsl/history.jsonl.
    def __init__(project_dir)  # CC=1
    def record(event)  # CC=1
    def record_event(event_type)  # CC=1
    def decision_signature()  # CC=2
    def has_recent_signature(signature, limit)  # CC=5
class HistoryReader:  # Read-only access to .redsl/history.jsonl for querying and de
    def __init__(project_dir)  # CC=1
    def load_events()  # CC=5
    def filter_by_file(target_file)  # CC=3
    def filter_by_type(event_type)  # CC=3
    def has_recent_proposal(target_file, action)  # CC=7
    def has_recent_ticket(title_prefix)  # CC=7
    def generate_decision_report()  # CC=11 ⚠
```

### `redsl.consciousness_loop` (`redsl/consciousness_loop.py`)

```python
def main_loop()  # CC=4, fan=6
class ConsciousnessLoop:  # Ciągła pętla „świadomości" agenta.
    def __init__(project_dir, interval_seconds, config)  # CC=2
    def run()  # CC=5
    def _inner_thought(cycle)  # CC=3
    def _self_assessment(cycle)  # CC=3
    def _profile_performance(cycle)  # CC=3
    def stop()  # CC=1
```

### `redsl.config` (`redsl/config.py`)

```python
def _default_llm_model()  # CC=6, fan=1
def _resolve_provider_key(model)  # CC=6, fan=3
class LLMConfig:  # Konfiguracja warstwy LLM.
    def is_local()  # CC=1
    def api_key()  # CC=1
    def api_key(value)  # CC=1
class MemoryConfig:  # Konfiguracja systemu pamięci.
class AnalyzerConfig:  # Konfiguracja analizatora kodu.
class RefactorConfig:  # Konfiguracja silnika refaktoryzacji.
class AgentConfig:  # Główna konfiguracja agenta.
    def from_env(cls)  # CC=3
```

### `redsl.orchestrator` (`redsl/orchestrator.py`)

```python
class CycleReport:  # Raport z jednego cyklu refaktoryzacji.
class RefactorOrchestrator:  # Główny orkiestrator — „mózg" systemu.
    def __init__(config)  # CC=2
    def run_cycle(project_dir, max_actions, use_code2llm, validate_regix, rollback_on_failure, use_sandbox, target_file)  # CC=1
    def run_from_toon_content(project_toon, duplication_toon, validation_toon, source_files, max_actions)  # CC=1
    def add_custom_rules(rules_yaml)  # CC=1
    def _resolve_limits(project_dir, default_max)  # CC=8
```

## Intent

ReDSL — Refactor + DSL + Self-Learning. LLM-powered autonomous code refactoring.
