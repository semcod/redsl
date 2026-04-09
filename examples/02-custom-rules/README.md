# ReDSL Example 02: Custom DSL Rules

This example demonstrates how to define and use custom DSL rules for refactoring decisions.

## Features

- **Programmatic Rules** — Define rules using Python DSL classes
- **YAML Rules** — Load rules from YAML/dict format
- **Rule Composition** — Combine custom rules with built-in defaults
- **Rule Evaluation** — Test rules against sample metrics

## Running the Example

```bash
cd examples/02-custom-rules
python main.py
```

## Example Rules

### 1. Security Audit (Python-defined)
```python
Rule(
    name="security_audit_long_functions",
    conditions=[
        Condition("cyclomatic_complexity", Operator.GT, 20),
        Condition("is_public_api", Operator.EQ, True),
    ],
    action=RefactorAction.EXTRACT_FUNCTIONS,
    priority=0.95,
)
```

### 2. Tiny Wrapper Inlining (Python-defined)
```python
Rule(
    name="inline_tiny_wrappers",
    conditions=[
        Condition("module_lines", Operator.LT, 5),
        Condition("function_count", Operator.EQ, 1),
    ],
    action=RefactorAction.INLINE_FUNCTION,
    priority=0.40,
)
```

### 3. Max Module Size (YAML-defined)
```yaml
name: enforce_max_module_size
when:
  module_lines:
    gt: 600
then:
  action: split_module
  priority: 0.92
```

### 4. Untested Complex Code (YAML-defined)
```yaml
name: flag_untested_complex
when:
  cyclomatic_complexity:
    gt: 10
  linter_warnings:
    gt: 0
then:
  action: add_type_hints
  priority: 0.55
```

## Rule Operators

- `GT` — Greater than
- `LT` — Less than
- `EQ` — Equal to
- `GTE` — Greater than or equal
- `LTE` — Less than or equal

## Actions

- `EXTRACT_FUNCTIONS` — Break large functions into smaller ones
- `INLINE_FUNCTION` — Inline small wrapper functions
- `SPLIT_MODULE` — Split large modules
- `ADD_TYPE_HINTS` — Add type annotations

## Sample Contexts

The example evaluates rules against 3 sample contexts:
1. `api/auth.py:verify_token` — High CC public API
2. `utils/wrap.py:log_wrapper` — Tiny wrapper
3. `services/mega_service.py` — Large module with lint issues
