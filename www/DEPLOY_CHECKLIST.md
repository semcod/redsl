# REDSL Panel — Deployment Checklist (Path A: First Client)

> 10-dniowy sprint za Tobą. To jest checklista żeby wdrożyć na prod i przetestować end-to-end przed pierwszym klientem.

## Faza 1: Pre-deployment (lokalnie)

### 1.1 Wymagania
- [ ] VPS z Ubuntu 22.04+ / Debian 12+
- [ ] Docker + Docker Compose zainstalowane
- [ ] Domena z DNS wskazującym na VPS
- [ ] Let's Encrypt (certbot) gotowy
- [ ] MySQL 8.0+ (może być Docker)

### 1.2 Sekrety (wygeneruj lokalnie, zapisz w 1Password)
```bash
# ENCRYPTION_KEY (32 bajty hex)
php -r "echo bin2hex(random_bytes(32));"
# Example: a1b2c3d4e5f6... (64 hex chars)

# Admin password hash
php -r "echo password_hash('TwojeSilneHaslo123!', PASSWORD_BCRYPT);"
```

**Backup offline:** Zapisz `ENCRYPTION_KEY` na papierze/USB — bez niego tokeny GitHub są martwe.

---

## Faza 2: Deploy (VPS)

### 2.1 Klon + build
```bash
git clone https://github.com/semcod/redsl /opt/redsl
cd /opt/redsl/www

# Skopiuj .env i wypełnij
mv .env.example .env
nano .env  # wypełnij WSZYSTKO
```

**Wymagane zmienne w .env:**
```
DB_HOST=db  # jeśli MySQL w Docker Compose
DB_NAME=redsl
DB_USER=redsl_user
DB_PASS=<generuj: openssl rand -base64 24>
ENCRYPTION_KEY=<64 hex chars z kroku 1.2>
ADMIN_USER=admin
ADMIN_PASS_HASH=<bcrypt z kroku 1.2>
CONTACT_EMAIL=kontakt@twojadomena.pl
MAIL_FROM=no-reply@twojadomena.pl
INVOICE_COMPANY_NAME="Twoja Firma Sp. z o.o."
INVOICE_COMPANY_TAX_ID=PL1234567890
INVOICE_COMPANY_ADDRESS="ul. Twoja 123, 00-001 Warszawa"
```

### 2.2 Docker Compose (prod)
Create `/opt/redsl/www/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    container_name: redsl-mysql
    environment:
      MYSQL_ROOT_PASSWORD: <root password>
      MYSQL_DATABASE: redsl
      MYSQL_USER: redsl_user
      MYSQL_PASSWORD: <z .env DB_PASS>
    volumes:
      - mysql_data:/var/lib/mysql
      - ./migrations:/docker-entrypoint-initdb.d:ro
    ports:
      - "127.0.0.1:3306:3306"  # tylko localhost
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    container_name: redsl-app
    ports:
      - "127.0.0.1:8080:80"  # nginx proxy do 443
    volumes:
      - ./.env:/var/www/html/.env:ro
      - app_var:/var/www/html/var
    environment:
      DB_HOST: db
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  # Opcjonalnie: nginx reverse proxy + SSL
  nginx:
    image: nginx:alpine
    container_name: redsl-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  mysql_data:
  app_var:
```

### 2.3 Uruchomienie
```bash
cd /opt/redsl/www
docker-compose -f docker-compose.prod.yml up -d

# Sprawdź logi
docker-compose logs -f app
```

### 2.4 Cron (na hoście, nie w kontenerze)
```bash
# Edytuj crontab roota
sudo crontab -e

# Dodaj (dostosuj ścieżkę do docker exec):
*/10 * * * * cd /opt/redsl && docker exec redsl-app php cron/scan-worker.php >> var/logs/scan-cron.log 2>&1
0 6 1 * * cd /opt/redsl && docker exec redsl-app php cron/invoice-generator.php >> var/logs/invoice-cron.log 2>&1
```

### 2.5 HTTPS (Let's Encrypt)
```bash
# Na hoście VPS
sudo apt install certbot
sudo certbot certonly --standalone -d twojadomena.pl -d www.twojadomena.pl

# Certy będą w /etc/letsencrypt/live/twojadomena.pl/
# nginx.conf musi je używać (patrz template poniżej)
```

---

## Faza 3: Smoke Test (end-to-end)

> Uruchom ten checklist ręcznie przed pierwszym klientem. Każdy krok musi przejść.

### 3.1 Przygotowanie testowe
```bash
# Utwórz testowego klienta ręcznie (lub przez admin)
# Weź własne repo GitHub jako test project
# Upewnij się że masz token GitHub z repo scope
```

### 3.2 Checklista A-Z

| Krok | Akcja | Oczekiwany wynik | Status |
|------|-------|------------------|--------|
| 1 | Wejdź na `https://twojadomena.pl/admin/` | Login prompt (Basic Auth) | [ ] |
| 2 | Zaloguj się adminem | Widzisz dashboard | [ ] |
| 3 | **Dodaj klienta** przez `admin/clients.php` → "Nowy klient" | Klient w tabeli, status "lead" | [ ] |
| 4 | **Generuj NDA** przez `admin/contracts.php` → "Nowa umowa" → type=NDA | PDF w `var/contracts/nda-{id}-{token}.pdf` | [ ] |
| 5 | **Dodaj projekt** przez `admin/projects.php` z własnym repo GitHub | Projekt w tabeli, status "active" | [ ] |
| 6 | **Odpal scan ręcznie**: `docker exec redsl-app php cron/scan-worker.php` | Scan completed, artifacts w `var/scans/YYYY/MM/scan-{id}/` | [ ] |
| 7 | **Sprawdź tickets**: `admin/tickets.php` | Widzisz tickety z `price_pln=10.00` | [ ] |
| 8 | **Oznacz ticket jako merged** (ręcznie w DB lub przez admin):<br>`UPDATE tickets SET status='merged', merged_at=NOW() WHERE id={id};` | Status "merged" | [ ] |
| 9 | **Generuj fakturę** (backdate):<br>`docker exec redsl-app php -r "require 'cron/invoice-generator.php'"` lub zmień daty w kodzie na test | Faktura w `admin/invoices.php`, PDF w `var/invoices/` | [ ] |
| 10 | **Sprawdź PDF faktury** | Dane firmy, pozycja ticket, kwota, VAT 23% | [ ] |

**Jeśli którykolwiek krok failuje — NIE wdrażaj dla klienta. Napraw najpierw.**

---

## Faza 4: Go-live

### 4.1 Pre-flight
- [ ] Smoke test przeszedł wszystkie kroki 1-10
- [ ] Backup `.env` i `ENCRYPTION_KEY` jest offline
- [ ] Logi crona działają: `tail -f /opt/redsl/var/logs/scan-cron.log`
- [ ] Domena działa z HTTPS (sprawdź cert)
- [ ] Rate limiting działa (sprawdź `check_rate_limit()`)

### 4.2 Pierwszy klient (procedura)
1. Lead wpada przez formularz kontaktowy
2. Ty dodajesz go w `admin/clients.php` (status "lead")
3. Wysyłasz NDA przez `admin/contracts.php` → generuj PDF → email
4. Po podpisaniu NDA: zmień status klienta na "active"
5. Dodaj projekt z repo klienta (token GitHub klienta lub własny z repo scope)
6. Scan worker złapie projekt automatycznie (co 10 min)
7. Ty przeglądasz tickety w `admin/tickets.php`, approvujesz te do zrobienia
8. Jak PR jest merged — ticket sam się oznacza (manualnie teraz, webhook później)
9. Faktura generuje się 1. dnia miesiąca automatycznie

---

## Znane braki (Path A akceptowalne)

| Gap | Ryzyko | Mitigacja |
|-----|--------|-----------|
| Brak audit_log INSERTów | Nie ma logu kto co zmienił | Path B: dodać logging do Repository |
| Brak webhook GitHub | Ręczne oznaczanie merged | Path B: dodać endpoint webhook |
| CC=17 w validateConfig, form() | Dług techniczny | Path B: refactoring |
| Ręczne approvowanie ticketów | Wymaga Twojej uwagi | To feature, nie bug — chcesz kontroli |

---

## Emergency runbook (gdy coś nie działa)

### Cron nie generuje scanów
```bash
# Sprawdź czy cron działa
sudo tail -f /var/log/syslog | grep CRON

# Sprawdź logi aplikacji
docker exec redsl-app tail -f /var/www/html/var/logs/scan-worker.log

# Sprawdź czy są projekty do scanu
docker exec redsl-mysql mysql -uredsl_user -p -e "SELECT id, name, next_scan_at FROM redsl.projects WHERE status='active';"
```

### Nie ma nowych ticketów po scanie
```bash
# Sprawdź czy scan się ukończył
docker exec redsl-mysql mysql -uredsl_user -p -e "SELECT id, project_id, status, error_message FROM redsl.scan_runs ORDER BY id DESC LIMIT 5;"

# Sprawdź artifacts na dysku
docker exec redsl-app ls -la /var/www/html/var/scans/$(date +%Y/%m)/
```

### Faktura się nie wygenerowała
```bash
# Sprawdź czy są merged tickety bez faktury
docker exec redsl-mysql mysql -uredsl_user -p -e "
SELECT t.id, t.project_id, t.merged_at, t.price_pln 
FROM redsl.tickets t 
LEFT JOIN redsl.invoice_items ii ON ii.ticket_id = t.id 
WHERE t.status='merged' AND t.merged_at IS NOT NULL AND ii.id IS NULL;"

# Uruchom invoice generator ręcznie z verbose
docker exec redsl-app php cron/invoice-generator.php
```

### Zagubiony ENCRYPTION_KEY
**Nie da się odzyskać tokenów GitHub.** Musisz:
1. Wygenerować nowy klucz: `php -r "echo bin2hex(random_bytes(32));"`
2. Uaktualnić `.env`
3. Restart kontenera: `docker-compose restart app`
4. Poprosić wszystkich klientów o ponowne podanie tokenów (lub użyć własnych)

---

## Po deploy (Path B backlog)

Dodaj do planfile:
- [ ] Audit logging do Repository (INSERT audit_log przy każdym write)
- [ ] GitHub webhook endpoint `/webhook/github` dla auto-merged
- [ ] Refactor validateConfig (CC 17 → 4)
- [ ] Refactor form() w app.js (CC 17 → 4)
- [ ] Auto-SSL renewal (certbot cron)
- [ ] Monitoring: alert gdy scan failuje 3x z rzędu

---

**Created:** 2026-04-20  
**Path:** A (Fast to First Client)  
**Status:** Ready for deploy
