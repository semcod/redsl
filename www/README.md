# REDSL Landing Page — Deployment

Landing page z paneliem SaaS: `index.php` + `style.css` + `app.js` + panel konfiguracji + NDA + wybór propozycji. Działa na każdym shared hostingu z PHP 8.1+.

## Szybki start (lokalnie)

```bash
cd landing
cp .env.example .env
# Edytuj .env — na razie wystarczy CONTACT_EMAIL
php -S localhost:8000
```

Otwórz `http://localhost:8000`. Formularz kontaktowy użyje lokalnego `mail()` — na komputerze prawdopodobnie nie wyśle nic, ale strona się wyrenderuje.

## Produkcja — shared hosting (np. polskie home.pl, cyberfolks, hekko)

1. **Wrzuć pliki przez FTP/SFTP** do katalogu public (zwykle `public_html/`, `domains/twojadomena.pl/public_html/`, etc.). Lista plików:
   - `index.php` — landing page
   - `style.css`, `app.js` — assets
   - `config-editor.php` — edytor konfiguracji
   - `config-api.php` — API konfiguracji
   - `propozycje.php` — wybór ticketów
   - `nda-form.php` — automatyczne NDA
   - `polityka-prywatnosci.php`, `regulamin.php` — strony prawne
   - `.htaccess` — rewrite rules
   - `.env` *(stworzony z `.env.example`)*
2. **Uprawnienia na `.env`**: `chmod 600 .env` (tylko właściciel czyta).
3. **Sprawdź że `.env` nie jest widoczny** — odwiedź `https://twojadomena.pl/.env` — powinno być 403. Jeśli 200, twój hosting ignoruje `.htaccess` i musisz użyć innej metody (wynieść `.env` poza public lub rename).
4. **Email** — jeśli hosting wspiera `mail()` z twojej domeny, formularz będzie działać. Jeśli maile lądują w spamie, skonfiguruj SPF + DKIM w panelu DNS.
5. **HTTPS** — każdy nowoczesny hosting oferuje Let's Encrypt w panelu. Włącz i odkomentuj `Strict-Transport-Security` oraz blok "Force HTTPS" w `.htaccess`.

## Produkcja — własny VPS (nginx + PHP-FPM)

```nginx
server {
    listen 443 ssl http2;
    server_name twojadomena.pl;

    root /var/www/redsl-landing;
    index index.php;

    # Block .env and other sensitive files
    location ~ /\.(env|git|htaccess) {
        deny all;
        return 404;
    }

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }

    # Static assets cache
    location ~* \.(css|js|svg|png|jpg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    ssl_certificate     /etc/letsencrypt/live/twojadomena.pl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/twojadomena.pl/privkey.pem;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}

server {
    listen 80;
    server_name twojadomena.pl;
    return 301 https://$host$request_uri;
}
```

## Konfiguracja GitHub OAuth

Bez tego przycisk "Zaloguj przez GitHub" pokaże komunikat "OAuth jeszcze nie skonfigurowany" — formularz kontaktowy działa niezależnie, więc nie jest to blocker do uruchomienia strony.

### Kroki

1. Idź na https://github.com/settings/developers
2. **New OAuth App**
3. Wypełnij:
   - **Application name**: `REDSL Landing`
   - **Homepage URL**: `https://twojadomena.pl`
   - **Authorization callback URL**: `https://twojadomena.pl/`
     (to samo co `GITHUB_REDIRECT_URI` w `.env` — GitHub sam dopisze `?code=...&state=...`, `index.php` to wykryje)
4. **Register application**
5. Skopiuj **Client ID** → wklej w `.env` jako `GITHUB_CLIENT_ID`
6. **Generate a new client secret** → skopiuj → wklej jako `GITHUB_CLIENT_SECRET`
7. Restart PHP-FPM (VPS) lub wystarczy poczekać 1 minutę (shared hosting cache)

### Co dostaje strona po OAuth

- Login GitHub użytkownika
- Imię (jeśli ustawione publicznie)
- Email (jeśli publiczny lub w scope `user:email`)
- Firma (jeśli ustawiona)
- Liczba publicznych repo

Wysyłane na `CONTACT_EMAIL` jako notyfikacja. To jest lead — teraz twoja kolej skontaktować się z nimi i zeskanować ich top repo.

## Bezpieczeństwo — checklist przed publikacją

- [ ] `.env` ma `chmod 600`
- [ ] `.env` NIE jest w repo (`.gitignore` zawiera `.env`)
- [ ] Odwiedzenie `/.env` zwraca 403 lub 404
- [ ] HTTPS włączone, redirect 80→443 działa
- [ ] `CONTACT_EMAIL` ustawiony i otrzymuje testowe maile z formularza
- [ ] GitHub OAuth app ma dokładnie ten sam `Authorization callback URL` co `.env`
- [ ] CSP w `.htaccess` nie blokuje żadnych krytycznych zasobów (sprawdź konsolę przeglądarki)

## Testowanie

### Formularz kontaktowy
1. Wypełnij formularz z prawidłowym emailem
2. Sprawdź skrzynkę `CONTACT_EMAIL`
3. Sprawdź że dwukrotne submit w ciągu 60s zwraca "Zaczekaj chwilę"

### OAuth flow
1. Kliknij "Zaloguj przez GitHub"
2. Autoryzuj
3. Powinieneś wrócić na stronę z zielonym bannerem "Cześć @twój-login"
4. Sprawdź że dostałeś notyfikację na `CONTACT_EMAIL`

### Honeypot anty-spam
Formularz ma ukryte pole `website`. Boty które scrape'ują HTML często je wypełniają. Jeśli jest wypełnione, strona pokazuje success ale nic nie wysyła.

## Customizacja

**Zmiana kolorów** — `style.css` sekcja `:root`. Wszystko na zmiennych CSS. Najważniejsze:
- `--paper` = tło (kremowe)
- `--ink` = tekst główny
- `--red` = akcent (pieczątki, linie)

**Zmiana fontów** — `index.php` sekcja `<link>` (Google Fonts) + `style.css` zmienne `--font-*`.

**Zmiana copy** — wszystko po polsku w `index.php`. Nie ma i18n, bo to mała strona. Dla EN wersji po prostu sklonuj `index.php` jako `index-en.php`.

**Zmiana cennika** — sekcja `.pricing` w `index.php`. Jeśli zmienisz liczby, pamiętaj zmienić też w sekcji FAQ i kontakt.

## Testy

### PHPUnit (backend logic)

```bash
cd www
composer install
composer test              # wszystkie testy
composer test:gui          # tylko testy GUI
```

### Playwright (E2E browser tests)

```bash
cd www/tests/e2e
npm install
npm run install:browsers
npm run test               # headless
npm run test:ui            # interaktywny tryb
```

Szczegóły w [`tests/README_TESTS.md`](tests/README_TESTS.md).

## Panel SaaS — funkcje

| Strona | URL | Opis |
|--------|-----|------|
| **Config Editor** | `/config-editor.php` | Edytor YAML konfiguracji z walidacją i backupami |
| **Config API** | `/config-api.php` | REST API do walidacji, historii, diff |
| **Wybór propozycji** | `/propozycje.php` | Panel wyboru ticketów refaktoryzacji |
| **NDA** | `/nda-form.php` | Automatyczne generowanie umowy NDA (NIP → dane firmy) |
| **Polityka prywatności** | `/polityka-prywatnosci` | Strona prawna |
| **Regulamin** | `/regulamin` | Strona prawna |

### Config Editor
- Edycja `redsl.config.yaml` z syntax highlighting
- Redakcja sekretów (nigdy nie pokazuje wartości)
- Automatyczne backupy przy zapisie
- Wskaźniki poziomów ryzyka
- Walidacja YAML + schema

### Wybór propozycji
- Klient otrzymuje email z linkiem
- Wybór format: `1, 3, 7, 12-15, 24` lub `wszystkie`
- Kalkulacja ceny: 10 zł / ticket
- Potwierdzenie → generowanie zleceń

### NDA Form
- Wprowadzenie NIP → auto-uzupełnienie danych (GUS REGON API)
- Generowanie PDF umowy
- Upload podpisanego dokumentu lub email

## Znane ograniczenia

- `mail()` — domyślna funkcja PHP często ląduje w spamie. Dla poważnego użytku podłącz SMTP (komentarze w `.env.example`).
- Rate limiting jest per-session, nie per-IP. Zdeterminowany bot może obejść czyszcząc cookies. Dla prostej strony wystarczy.
- Brak CAPTCHA — honeypot i rate-limit zazwyczaj wystarczą dla ~99% botów, ale jeśli będziesz miał problem ze spamem, dorzuć hCaptcha (darmowy, niekomercyjne ograniczenia dalekie od landing page skali).
- Brak analityki — celowo. Jeśli chcesz, dodaj Plausible lub Simple Analytics (nie Google Analytics — CSP tego nie przepuści bez zmian).

## Licencja

Kod landing page jest twój. Używaj jak chcesz.
