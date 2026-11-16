#!/bin/sh
# Keystone Quest container start-up.
#  1. Points Apache at $PORT (Render sets this; defaults to 10000).
#  2. If KQ_DATA_DIR is set (a persistent disk on Render), copies in each bundled
#     adventure the first time it ships. Adventures you've edited are never
#     overwritten, and ones you've deleted aren't brought back.
#  3. Gives Apache permission to write adventures, then starts it.
set -e

APP_DIR="${KQ_APP_DIR:-/var/www/html}"
BUNDLED="$APP_DIR/adventures"
DATA="${KQ_DATA_DIR:-$BUNDLED}"
PORT="${PORT:-10000}"

if [ -f /etc/apache2/ports.conf ]; then
  sed -i "s/^Listen .*/Listen ${PORT}/" /etc/apache2/ports.conf
  sed -i "s/<VirtualHost \*:[0-9]*>/<VirtualHost *:${PORT}>/" /etc/apache2/sites-available/000-default.conf
fi

mkdir -p "$DATA"
if [ "$DATA" != "$BUNDLED" ]; then
  SEEDED="$DATA/.seeded"
  touch "$SEEDED"
  for f in "$BUNDLED"/*.json; do
    [ -e "$f" ] || continue
    name=$(basename "$f")
    if ! grep -qxF "$name" "$SEEDED"; then
      [ -e "$DATA/$name" ] || { cp "$f" "$DATA/$name"; echo "Keystone Quest: added bundled adventure $name"; }
      echo "$name" >> "$SEEDED"
    fi
  done
else
  echo "Keystone Quest: KQ_DATA_DIR is not set, so adventures are saved inside the container and will be lost on redeploy."
fi

if [ -z "$KQ_EDIT_PASSWORD" ] && [ ! -f "$APP_DIR/config.php" ]; then
  echo "Keystone Quest: set KQ_EDIT_PASSWORD to enable the adventure editor."
fi

if id www-data >/dev/null 2>&1; then chown -R www-data:www-data "$DATA"; fi

exec docker-php-entrypoint "$@"
