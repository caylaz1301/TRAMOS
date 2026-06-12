FROM php:8.2-apache-bookworm

ENV APACHE_DOCUMENT_ROOT=/var/www/html

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libc-client-dev \
        libfreetype6-dev \
        libicu-dev \
        libjpeg62-turbo-dev \
        libkrb5-dev \
        libonig-dev \
        libpng-dev \
        libxml2-dev \
        libzip-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-configure imap --with-kerberos --with-imap-ssl \
    && docker-php-ext-install -j"$(nproc)" \
        gd \
        imap \
        intl \
        mbstring \
        mysqli \
        opcache \
        pdo_mysql \
        zip \
    && a2enmod rewrite headers expires \
    && rm -rf /var/lib/apt/lists/*

COPY deploy/apache/osticket.conf /etc/apache2/conf-available/tramos-osticket.conf
COPY deploy/osticket-entrypoint.sh /usr/local/bin/tramos-osticket-entrypoint

RUN a2enconf tramos-osticket \
    && chmod +x /usr/local/bin/tramos-osticket-entrypoint

ENTRYPOINT ["tramos-osticket-entrypoint"]
CMD ["apache2-foreground"]
