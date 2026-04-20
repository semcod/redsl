FROM php:8.3-apache

# Install extensions: YAML + PDO MySQL
RUN apt-get update && apt-get install -y libyaml-dev git unzip \
    && docker-php-ext-install pdo_mysql \
    && pecl install yaml \
    && docker-php-ext-enable yaml pdo_mysql \
    && rm -rf /var/lib/apt/lists/*

# Instalacja Composera
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Włącz mod_rewrite dla .htaccess
RUN a2enmod rewrite

# Ustaw DocumentRoot na /var/www/html (domyślnie już tak jest)
# ale zmień AllowOverride na All aby .htaccess działał
RUN sed -i 's/AllowOverride None/AllowOverride All/g' /etc/apache2/apache2.conf

# Skopiuj pliki aplikacji
COPY . /var/www/html/

# Zainstaluj zależności PHP (PHPMailer) - jeśli composer.json istnieje
RUN if [ -f /var/www/html/composer.json ]; then cd /var/www/html && composer install --no-dev --optimize-autoloader 2>/dev/null || true; fi

# Ustaw uprawnienia
RUN chown -R www-data:www-data /var/www/html \
    && chmod 600 /var/www/html/.env

# Blokuj dostęp do .env przez Apache (dodatkowe zabezpieczenie obok .htaccess)
RUN echo '<FilesMatch "^\.env$">\n    Order allow,deny\n    Deny from all\n</FilesMatch>' >> /etc/apache2/conf-available/env-deny.conf \
    && a2enconf env-deny

EXPOSE 80

# Uruchom Apache
CMD ["apache2-foreground"]
