# Keystone Quest: PHP + Apache image for Render (or any Docker host).
FROM php:8.3-apache

# Apache: allow the repo's .htaccess files, enable the headers module they use,
# and stop advertising version numbers. PHP: production settings.
RUN a2enmod headers \
 && printf '%s\n' \
      'ServerName localhost' \
      'ServerTokens Prod' \
      'ServerSignature Off' \
      '<Directory /var/www/html>' \
      '  AllowOverride All' \
      '</Directory>' \
      > /etc/apache2/conf-available/keystone.conf \
 && a2enconf keystone \
 && mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini" \
 && sed -i 's/^expose_php = On/expose_php = Off/' "$PHP_INI_DIR/php.ini"

COPY --chown=www-data:www-data . /var/www/html/
RUN mv /var/www/html/docker/entrypoint.sh /usr/local/bin/kq-entrypoint \
 && chmod +x /usr/local/bin/kq-entrypoint \
 && rm -rf /var/www/html/docker

# Render routes traffic to $PORT (10000 unless you change it).
ENV PORT=10000
EXPOSE 10000

ENTRYPOINT ["kq-entrypoint"]
CMD ["apache2-foreground"]
