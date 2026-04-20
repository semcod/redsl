<!-- code2docs:start --># www

![version](https://img.shields.io/badge/version-0.1.0-blue) ![php](https://img.shields.io/badge/php-any-777BB4) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-38-green)
> **38** functions | **0** classes | **22** files | CC̄ = 3.9

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
├── project
├── nda-wzor
├── polityka-prywatnosci
├── email-notifications
    ├── index
    ├── index
    ├── invoice-generator
    ├── auth
├── propozycje
├── config-editor
    ├── tickets
    ├── scan-worker
├── regulamin
├── config-api
    ├── scans
    ├── invoices
    ├── clients
├── nda-form
├── app
    ├── projects
    ├── contracts
├── index
```

## API Overview

### Functions

- `generateProposalEmail()` — —
- `sendProposalEmail()` — —
- `generateAccessToken()` — —
- `verifyAccessToken()` — —
- `validateCsrfToken()` — —
- `parseSelection()` — —
- `h()` — —
- `loadConfig()` — —
- `saveConfig()` — —
- `getNestedValue()` — —
- `getRiskLevel()` — —
- `validateConfig()` — —
- `getHistory()` — —
- `redactSecrets()` — —
- `fetchCompanyData()` — —
- `h()` — —
- `generateNDAText()` — —
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
📄 `admin.projects`
📄 `admin.scans`
📄 `admin.tickets`
📄 `app` (14 functions)
📄 `blog.index`
📄 `config-api` (3 functions)
📄 `config-editor` (4 functions)
📄 `cron.invoice-generator`
📄 `cron.scan-worker`
📄 `email-notifications` (4 functions)
📄 `index` (7 functions)
📄 `nda-form` (3 functions)
📄 `nda-wzor`
📄 `polityka-prywatnosci`
📄 `project`
📄 `propozycje` (2 functions)
📄 `regulamin`

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