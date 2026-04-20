# GUI Tests for ReDSL Web Interface

## Test Structure

```
www/tests/
├── ConfigEditorTest.php          # PHPUnit: Config editor backend
├── ProposalSelectionTest.php     # PHPUnit: Proposal parser logic
├── NdaFormTest.php               # PHPUnit: NDA form validation
├── ConfigApiTest.php             # PHPUnit: Config API endpoints
├── RedslApiProxyTest.php         # PHPUnit: /api/redsl.php proxy (redsl-api integration)
├── e2e/
│   ├── playwright.config.js      # Playwright configuration
│   ├── smoke-path.spec.js        # E2E: Smoke test (main paths)
│   ├── admin-panel.spec.js       # E2E: Admin panel
│   ├── github-login-full-flow.spec.js  # E2E: GitHub OAuth full flow
│   ├── config-editor.spec.js.disabled
│   ├── proposals.spec.js.disabled
│   └── nda-form.spec.js.disabled
└── README_TESTS.md               # This file
```

## PHPUnit Tests (Backend Logic)

### Installation

```bash
cd www
composer install
```

### Run All Tests

```bash
composer test
# or
./vendor/bin/phpunit tests/
```

### Run GUI-specific Tests

```bash
composer test:gui
# or
./vendor/bin/phpunit tests/ --filter 'ConfigEditor|ProposalSelection|NdaForm|ConfigApi'
```

### Run Individual Test Classes

```bash
./vendor/bin/phpunit tests/ConfigEditorTest.php
./vendor/bin/phpunit tests/ProposalSelectionTest.php
./vendor/bin/phpunit tests/NdaFormTest.php
./vendor/bin/phpunit tests/ConfigApiTest.php
```

### Test Coverage

**ConfigEditorTest.php** (7 tests)
- ✅ Config editor returns valid HTML
- ✅ Config initialization creates default config
- ✅ Secret redaction in display
- ✅ Risk level colors defined
- ✅ YAML validation
- ✅ Backup creation on save

**ProposalSelectionTest.php** (9 tests)
- ✅ Proposal list rendering
- ✅ Selection parser - single items
- ✅ Selection parser - ranges
- ✅ Selection parser - mixed format
- ✅ Selection parser - empty
- ✅ Price calculation
- ✅ Effort labels
- ✅ Form submission
- ✅ "All" and "under 15" selections

**NdaFormTest.php** (9 tests)
- ✅ NIP validation - valid format
- ✅ NIP validation - invalid format
- ✅ NIP cleaning (spaces, dashes)
- ✅ Company data fetching (mock)
- ✅ NDA text generation
- ✅ Form data validation
- ✅ Session data storage
- ✅ Step progression logic
- ✅ HTML sanitization

**ConfigApiTest.php** (9 tests)
- ✅ Config validation - valid config
- ✅ Config validation - missing apiVersion
- ✅ Config validation - invalid apiVersion
- ✅ Config validation - invalid secret ref
- ✅ Secret redaction in API response
- ✅ Fingerprint generation
- ✅ History listing
- ✅ Diff calculation
- ✅ JSON response format

**RedslApiProxyTest.php** (17 tests)
- ✅ resolve_project: valid project name
- ✅ resolve_project: strips path traversal (`../../../etc/passwd`)
- ✅ resolve_project: empty returns false
- ✅ resolve_project: only special chars returns false
- ✅ resolve_project: custom workspace
- ✅ Mock curl OK response (200)
- ✅ Mock curl error response (502)
- ✅ Health response structure
- ✅ Analyze response contains expected fields
- ✅ max_actions clamped to 20
- ✅ max_actions default (5)
- ✅ dry_run defaults to true
- ✅ dry_run can be set to false
- ✅ Refactor payload uses `project_dir` (not `project_path`)
- ✅ Analyze payload uses `project_dir`
- ⚡ Live health endpoint (skipped if redsl-api unreachable)
- ⚡ Live analyze endpoint (skipped if redsl-api unreachable)

## Running PHPUnit via Docker (recommended)

Local PHP 8.4 may lack `dom`/`xml`/`yaml` extensions. Use Docker:

```bash
docker run --rm \
  -v $(pwd):/app \
  -w /app \
  --network host \
  php:8.3-cli \
  bash -c "apt-get update -qq && apt-get install -y -qq libyaml-dev && \
    pecl install yaml && docker-php-ext-enable yaml && \
    curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer && \
    composer install --no-interaction --ignore-platform-reqs -q && \
    ./vendor/bin/phpunit tests/ --no-coverage"
```

Z live testem redsl API:
```bash
docker run --rm \
  -v $(pwd):/app --network host -w /app php:8.3-cli \
  bash -c "... && REDSL_API_URL=http://127.0.0.1:8001 ./vendor/bin/phpunit tests/ --no-coverage"
```

## E2E Tests with Playwright

### Installation

```bash
# Install Playwright globally
npm install -g @playwright/test

# Install browser binaries
npx playwright install
```

### Run E2E Tests

```bash
# All E2E tests
composer test:e2e

# Specific browser
npx playwright test --project=chromium

# UI mode (interactive)
composer test:e2e:ui

# Debug mode
composer test:e2e:debug

# Specific test file
npx playwright test e2e/config-editor.spec.js
```

### E2E Test Coverage

**config-editor.spec.js**
- Display config editor page
- Show "No configuration" when config does not exist
- Create default config on button click
- Display risk levels in sidebar
- Redact secrets in display
- Allow editing and saving config
- Show common paths in sidebar
- Validate YAML syntax on save
- Display config info in sidebar
- Mobile responsiveness

**proposals.spec.js**
- Display proposal selection page
- Display proposal list
- Allow selecting "all" option
- Allow selecting "custom" option
- Display effort labels
- Display price for each proposal
- Show instructions
- Submit form with selection
- Parse single numbers correctly
- Parse ranges correctly
- Parse mixed format correctly
- Mobile responsiveness

**nda-form.spec.js**
- Display NDA form page
- Show step indicators
- Start at step 1
- Accept valid NIP
- Clean NIP from spaces and dashes
- Proceed to step 2 with demo NIP
- Show company data prefilled
- Require all fields in step 2
- Proceed to step 3 after filling form
- Show generated NDA text
- Have download button
- Have upload zone
- Validate email format
- Mobile responsiveness

### Environment Variables

```bash
# Custom base URL
BASE_URL=http://localhost:3000 npx playwright test

# CI mode (no UI, headless)
CI=true npx playwright test
```

## Quick Test Commands Summary

| Command | Purpose |
|---------|---------|
| `composer test` | Run all PHPUnit tests |
| `composer test:gui` | Run GUI-specific PHPUnit tests |
| `composer test:e2e` | Run all Playwright E2E tests |
| `composer test:e2e:ui` | Run E2E tests in UI mode |
| `composer test:e2e:debug` | Run E2E tests in debug mode |
| `npx playwright test --ui` | Interactive test runner |

## Adding New Tests

### PHPUnit Test

```php
<?php
use PHPUnit\Framework\TestCase;

class MyNewTest extends TestCase
{
    public function testSomething(): void
    {
        $this->assertTrue(true);
    }
}
```

### Playwright E2E Test

```javascript
const { test, expect } = require('@playwright/test');

test('should do something', async ({ page }) => {
  await page.goto('/my-page.php');
  await expect(page.locator('h1')).toContainText('My Page');
});
```

## CI/CD Integration

```yaml
# .github/workflows/gui-tests.yml
name: GUI Tests

on: [push, pull_request]

jobs:
  phpunit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: php-actions/composer@v6
        with:
          working_dir: www
      - run: cd www && ./vendor/bin/phpunit tests/

  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: cd www/tests/e2e && npx playwright install
      - run: cd www/tests/e2e && npx playwright test
```

## Troubleshooting

### PHP Extension: yaml

If tests fail with "yaml_parse() not found":
```bash
# Ubuntu/Debian
sudo apt-get install php-yaml

# Or use PECL
pecl install yaml
```

### Playwright: Missing browsers

```bash
npx playwright install
```

### Port conflicts

If port 8080 is in use, change in `playwright.config.js`:
```javascript
webServer: {
  command: 'php -S localhost:8081 -t ..',
  port: 8081,
}
```

## Test Status

| Test Suite | Status | Count |
|------------|--------|-------|
| PHPUnit: ConfigEditorTest | ✅ Pass | 7 tests |
| PHPUnit: ProposalSelectionTest | ✅ Pass | 9 tests |
| PHPUnit: NdaFormTest | ✅ Pass | 9 tests |
| PHPUnit: ConfigApiTest | ✅ Pass | 9 tests |
| PHPUnit: RedslApiProxyTest | ✅ Pass | 17 tests (2 live, skipped w/o API) |
| PHPUnit: PlaceholderTest | ✅ Pass | 1 test (skipped) |
| **PHPUnit Total** | **✅ 53/53 pass** | **53 tests** |
| Playwright E2E (active) | ✅ Ready | 3 suites |
| Playwright E2E (disabled) | ⏸ Disabled | 3 suites |
| **Python (redsl core)** | **✅ 690/690 pass** | **690 tests, 12 skipped** |

### Znane problemy

**`code2llm/core/analyzer.py` — regresja po refaktoryzacji LLM** (2026-04-20):
- Redsl refaktor usunął importy (`Optional`, `logging`, `concurrent.futures`) z pliku
- Objaw: `NameError: name 'Optional' is not defined` przy uruchomieniu `code2llm`
- Fix: `git checkout HEAD -- code2llm/core/analyzer.py` w repo `code2llm`
- Dotknięte testy: `test_bridges.py::test_generate_toon_files_on_redsl`, `test_pipeline.py::TestPipelinePerceive` (2 testy)

### Wymagania PHP

| Extension | Wymagane przez | Dostępność |
|-----------|---------------|------------|
| `yaml` (PECL) | ConfigApiTest, ConfigEditorTest | ❌ PHP 8.4 brak — użyj Docker |
| `dom`, `xml` | PHPUnit 10 core | ❌ PHP 8.4 brak — użyj Docker |
| `curl` | RedslApiProxyTest (live) | ✅ dostępne |
| `mbstring`, `json` | wszystkie | ✅ dostępne |
