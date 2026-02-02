#!/bin/sh
set -e

# Get environment from ENVIRONMENT variable, default to dev
ENV=${ENVIRONMENT:-dev}

# Replace the API gateway URL in nginx config based on environment
sed -i "s|api-gateway\.dev\.inventory\.local|api-gateway.${ENV}.inventory.local|g" /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g "daemon off;"
