#!/bin/sh

# Create directories for certbot
mkdir -p ./nginx/certbot/conf
mkdir -p ./nginx/certbot/www

# Start nginx
docker-compose -f docker-compose.prod.yml up -d nginx

# Get SSL certificate
docker-compose -f docker-compose.prod.yml run --rm certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email shivambmishra10@gmail.com \
    --agree-tos \
    --no-eff-email \
    -d api.travelwithghost.com

# Reload nginx to load the certificates
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload