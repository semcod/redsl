<!-- code2docs:start --># www

![version](https://img.shields.io/badge/version-0.1.0-blue) ![php](https://img.shields.io/badge/php-any-777BB4) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-66-green)
> **66** functions | **0** classes | **32** files | CC̄ = 3.5

> Auto-generated project documentation from source code analysis.

**Author:** ReDSL Team  
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
├── nda-wzor
├── install-plesk
├── project
├── smoke-test
├── test-plesk
├── polityka-prywatnosci
├── nda-form
├── config-editor
├── config-api
    ├── logs
    ├── user
    ├── access_token
├── propozycje
    ├── auth
├── regulamin
├── proposals
    ├── invoices
├── email-notifications
    ├── scans
    ├── index
    ├── clients
    ├── index
    ├── contracts
    ├── index
    ├── authorize
    ├── scan-worker
    ├── redsl
    ├── invoice-generator
    ├── projects
    ├── tickets
├── app
├── index
```

## API Overview

### Functions

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
- `fetchCompanyData()` — —
- `h()` — —
- `generateNDAText()` — —
- `loadConfig()` — —
- `saveConfig()` — —
- `getNestedValue()` — —
- `getRiskLevel()` — —
- `validateConfig()` — —
- `getHistory()` — —
- `redactSecrets()` — —
- `h()` — —
- `classForLevel()` — —
- `fmtSize()` — —
- `load_env_pl()` — —
- `env_pl()` — —
- `parseSelection_pl()` — —
- `h_pl()` — —
- `validateCsrfToken()` — —
- `load_env()` — —
- `env()` — —
- `parseSelection()` — —
- `h()` — —
- `generateProposalEmail()` — —
- `sendProposalEmail()` — —
- `generateAccessToken()` — —
- `verifyAccessToken()` — —
- `h()` — —
- `redsl_curl()` — —
- `json_out()` — —
- `resolve_project()` — —
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
- `load_env()` — —
- `env()` — —
- `h()` — —
- `csrf_token()` — —
- `check_rate_limit()` — —
- `send_notification()` — —
- `send_notification_smtp()` — —


## Project Structure

📄 `admin.auth` (1 functions)
📄 `admin.clients`
📄 `admin.contracts`
📄 `admin.index`
📄 `admin.invoices`
📄 `admin.logs` (3 functions)
📄 `admin.projects`
📄 `admin.scans`
📄 `admin.tickets`
📄 `api.redsl` (3 functions)
📄 `app` (15 functions)
📄 `blog.index`
📄 `client.index` (1 functions)
📄 `config-api` (6 functions)
📄 `config-editor` (4 functions)
📄 `cron.invoice-generator`
📄 `cron.scan-worker`
📄 `email-notifications` (4 functions)
📄 `index` (7 functions)
📄 `install-plesk`
📄 `mock-github.access_token`
📄 `mock-github.authorize`
📄 `mock-github.user`
📄 `nda-form` (3 functions)
📄 `nda-wzor`
📄 `polityka-prywatnosci`
📄 `project`
📄 `proposals` (4 functions)
📄 `propozycje` (4 functions)
📄 `regulamin`
📄 `smoke-test` (8 functions)
📄 `test-plesk` (3 functions)

## Requirements

- phpmailer/phpmailer ^6.9

## Contributing

**Contributors:**
- Tom Sapletta

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