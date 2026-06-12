#!/usr/bin/env sh
set -eu

config_file="/var/www/html/include/ost-config.php"

required_vars="
OSTICKET_SECRET_SALT
OSTICKET_ADMIN_EMAIL
OSTICKET_DB_HOST
OSTICKET_DB_NAME
OSTICKET_DB_USER
OSTICKET_DB_PASSWORD
"

for variable in $required_vars; do
    eval "value=\${$variable:-}"
    if [ -z "$value" ]; then
        echo "[TRAMOS osTicket] Variabel wajib $variable belum diisi." >&2
        exit 1
    fi
done

# Konfigurasi dibuat saat container start agar kredensial tidak tersimpan
# di source osTicket yang diunggah ke VPS.
cat > "$config_file" <<PHP
<?php
if (!strcasecmp(basename(\$_SERVER['SCRIPT_NAME']), basename(__FILE__))
        || !defined('INCLUDE_DIR')) {
    die('Direct access denied.');
}

define('OSTINSTALLED', true);
define('SECRET_SALT', '${OSTICKET_SECRET_SALT}');
define('ADMIN_EMAIL', '${OSTICKET_ADMIN_EMAIL}');
define('DBTYPE', 'mysql');
define('DBHOST', '${OSTICKET_DB_HOST}');
define('DBNAME', '${OSTICKET_DB_NAME}');
define('DBUSER', '${OSTICKET_DB_USER}');
define('DBPASS', '${OSTICKET_DB_PASSWORD}');
define('TABLE_PREFIX', '${OSTICKET_TABLE_PREFIX:-ost_}');
define('TRUSTED_PROXIES', '${OSTICKET_TRUSTED_PROXIES:-}');
define('LOCAL_NETWORKS', '${OSTICKET_LOCAL_NETWORKS:-127.0.0.0/24,172.29.0.0/24}');
define('SESSION_SESSID', 'OSTSESSID');
?>
PHP

chmod 0640 "$config_file"
chown root:www-data "$config_file"

exec docker-php-entrypoint "$@"
