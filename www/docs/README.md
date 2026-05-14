<!-- code2docs:start --># www

![version](https://img.shields.io/badge/version-0.1.0-blue) ![php](https://img.shields.io/badge/php-any-777BB4) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-181-green)
> **181** functions | **0** classes | **61** files | CC̄ = 4.0

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0  
**Repository:** [https://github.com/semcod/redsl](https://github.com/semcod/redsl)

## Installation

### Requirements

- PHP 8.0+
- [Composer](https://getcomposer.org/)

### From Source

```bash
git clone https://github.com/semcod/redsl
cd www
composer install
```

## Quick Start

Serve the project with your preferred PHP runtime (built-in server shown for local development):

```bash
php -S localhost:8000
```

Or with Docker Compose if a `docker-compose.yml` is provided:

```bash
docker compose up
```




## Architecture

```
www/
├── propozycje
├── nda-form
├── nda-wzor
├── smoke-test
├── README_CONFIG
├── DEPLOY_CHECKLIST
├── README_PROPozycje
├── Makefile
├── bootstrap
├── config-editor
├── README-PLESK
├── email-notifications
├── docker-compose
├── phpunit
├── install-plesk
├── proposals
├── polityka-prywatnosci
├── index
├── composer
├── README_NDA
├── tree
├── test-plesk
├── config-api
├── Dockerfile
├── project
├── regulamin
├── README
├── app
    ├── index
    ├── landing-page-copy
    ├── README
    ├── authorize
    ├── access_token
    ├── user
    ├── index
    ├── logs
    ├── tickets
    ├── index
    ├── invoices
    ├── auth
    ├── scans
    ├── contracts
    ├── clients
    ├── projects
    ├── en
    ├── de
    ├── pl
    ├── index
    ├── invoice-generator
    ├── scan-worker
    ├── index
    ├── redsl
    ├── prompt
        ├── toon
    ├── context
        ├── toon
        ├── toon
    ├── README
        ├── toon
        ├── toon
    ├── calls
```

## API Overview

### Functions

- `fetchCompanyData()` — —
- `h()` — —
- `extractNip()` — —
- `handleStep1()` — —
- `buildClientData()` — —
- `saveClient()` — —
- `createNdaContract()` — —
- `saveNdaToDatabase()` — —
- `storeStep2Data()` — —
- `handleStep2()` — —
- `generateNDAText()` — —
- `check_http()` — —
- `check_content()` — —
- `check_php_syntax()` — —
- `check_env_exists()` — —
- `check_encryption_key()` — —
- `check_directories()` — —
- `check_admin_auth()` — —
- `check_cron_scripts()` — —
- `env()` — —
- `h()` — —
- `csrf_token()` — —
- `check_rate_limit()` — —
- `h_ce()` — —
- `loadConfig()` — —
- `saveConfig()` — —
- `getNestedValue()` — —
- `getRiskLevel()` — —
- `generateProposalEmail()` — —
- `sendProposalEmail()` — —
- `generateAccessToken()` — —
- `verifyAccessToken()` — —
- `parseSelection()` — —
- `h()` — —
- `h_pp()` — —
- `send_notification()` — —
- `send_notification_smtp()` — —
- `check_status()` — —
- `check_contains()` — —
- `check_not_contains()` — —
- `validateConfig()` — —
- `getHistory()` — —
- `redactSecrets()` — —
- `loadConfig()` — —
- `sendError()` — —
- `handleValidate()` — —
- `handleHistory()` — —
- `computeFingerprint()` — —
- `handleShow()` — —
- `buildDiff()` — —
- `handleDiff()` — —
- `handleNotFound()` — —
- `h()` — —
- `masthead()` — —
- `target()` — —
- `form()` — —
- `emailField()` — —
- `nameField()` — —
- `repoField()` — —
- `submitBtn()` — —
- `setInvalid()` — —
- `validEmail()` — —
- `validRepo()` — —
- `io()` — —
- `details()` — —
- `flash()` — —
- `headline()` — —
- `y()` — —
- `callRedslApi()` — —
- `generateMarkdownReport()` — —
- `formatIssuesForEmail()` — —
- `formatIssuesForGitHub()` — —
- `showTab()` — —
- `copyToClipboard()` — —
- `downloadMarkdown()` — —
- `updateAsyncProgressStep()` — —
- `updateProgressStep()` — —
- `getCqrsStatus()` — —
- `connectWebSocket()` — —
- `h()` — —
- `h()` — —
- `classForLevel()` — —
- `fmtSize()` — —
- `validateCsrfToken()` — —
- `redsl_curl()` — —
- `json_out()` — —
- `resolve_project()` — —
- `build_mcp_subscription_payload()` — —
- `callRedslApi()` — —
- `generateMarkdownReport()` — —
- `formatIssuesForEmail()` — —
- `formatIssuesForGitHub()` — —
- `showTab()` — —
- `copyToClipboard()` — —
- `downloadMarkdown()` — —
- `updateAsyncProgressStep()` — —
- `updateProgressStep()` — —
- `getCqrsStatus()` — —
- `connectWebSocket()` — —
- `masthead()` — —
- `target()` — —
- `form()` — —
- `emailField()` — —
- `nameField()` — —
- `repoField()` — —
- `submitBtn()` — —
- `setInvalid()` — —
- `validEmail()` — —
- `validRepo()` — —
- `io()` — —
- `details()` — —
- `flash()` — —
- `headline()` — —
- `y()` — —
- `redsl_curl()` — —
- `json_out()` — —
- `resolve_project()` — —
- `build_mcp_subscription_payload()` — —
- `fetchCompanyData()` — —
- `h()` — —
- `extractNip()` — —
- `handleStep1()` — —
- `buildClientData()` — —
- `saveClient()` — —
- `createNdaContract()` — —
- `saveNdaToDatabase()` — —
- `storeStep2Data()` — —
- `handleStep2()` — —
- `generateNDAText()` — —
- `validateConfig()` — —
- `getHistory()` — —
- `redactSecrets()` — —
- `loadConfig()` — —
- `sendError()` — —
- `handleValidate()` — —
- `handleHistory()` — —
- `computeFingerprint()` — —
- `handleShow()` — —
- `buildDiff()` — —
- `handleDiff()` — —
- `handleNotFound()` — —
- `generateProposalEmail()` — —
- `sendProposalEmail()` — —
- `generateAccessToken()` — —
- `verifyAccessToken()` — —
- `classForLevel()` — —
- `fmtSize()` — —
- `validateCsrfToken()` — —
- `send_notification()` — —
- `send_notification_smtp()` — —
- `h_ce()` — —
- `saveConfig()` — —
- `getNestedValue()` — —
- `getRiskLevel()` — —
- `parseSelection()` — —
- `env()` — —
- `csrf_token()` — —
- `check_rate_limit()` — —
- `h_pp()` — —
- `check_http()` — —
- `check_content()` — —
- `check_php_syntax()` — —
- `check_env_exists()` — —
- `check_encryption_key()` — —
- `check_directories()` — —
- `check_admin_auth()` — —
- `check_cron_scripts()` — —
- `check_status()` — —
- `check_contains()` — —
- `check_not_contains()` — —
- `load_env()` — —


## Project Structure

📄 `DEPLOY_CHECKLIST`
📄 `Dockerfile`
📄 `Makefile`
📄 `README`
📄 `README-PLESK`
📄 `README_CONFIG`
📄 `README_NDA`
📄 `README_PROPozycje`
📄 `admin.auth` (2 functions)
📄 `admin.clients`
📄 `admin.contracts`
📄 `admin.index`
📄 `admin.invoices`
📄 `admin.logs` (3 functions)
📄 `admin.projects`
📄 `admin.scans`
📄 `admin.tickets`
📄 `api.redsl` (4 functions)
📄 `app` (15 functions)
📄 `blog.index`
📄 `bootstrap` (5 functions)
📄 `client.index` (1 functions)
📄 `composer`
📄 `config-api` (15 functions)
📄 `config-editor` (5 functions)
📄 `cron.invoice-generator`
📄 `cron.scan-worker`
📄 `docker-compose`
📄 `docs.README`
📄 `docs.landing-page-copy`
📄 `email-notifications` (4 functions)
📄 `i18n.de`
📄 `i18n.en`
📄 `i18n.pl`
📄 `index` (2 functions)
📄 `install-plesk`
📄 `klient.index`
📄 `marketing.index` (11 functions)
📄 `mock-github.access_token`
📄 `mock-github.authorize`
📄 `mock-github.user`
📄 `nda-form` (11 functions)
📄 `nda-wzor`
📄 `phpunit`
📄 `polityka-prywatnosci` (1 functions)
📄 `project`
📄 `project.README`
📄 `project.analysis.toon`
📄 `project.calls`
📄 `project.calls.toon`
📄 `project.context`
📄 `project.evolution.toon`
📄 `project.map.toon` (131 functions)
📄 `project.project.toon`
📄 `project.prompt`
📄 `proposals` (2 functions)
📄 `propozycje`
📄 `regulamin` (1 functions)
📄 `smoke-test` (8 functions)
📄 `test-plesk` (3 functions)
📄 `tree`

## Requirements

- phpmailer/phpmailer ^6.9

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Open an issue or pull request to get started.
### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/redsl
cd www

# Install dependencies
composer install

# Run tests
vendor/bin/phpunit
```


<!-- code2docs:end -->