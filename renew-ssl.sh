#!/bin/bash
# =============================================================================
# SSL Certificate Renewal Script for api.travelwithghost.com
# Run this on the AWS instance (13.200.20.177) to force-renew the certificate.
# =============================================================================

set -e

echo "🔒 Renewing SSL certificate for api.travelwithghost.com..."

# Force renew the certificate
docker-compose -f docker-compose.prod.yml run --rm certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email shivambmishra10@gmail.com \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d api.travelwithghost.com

echo "🔄 Reloading Nginx to pick up new certificate..."

# Reload nginx to use the new certificate
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

echo "✅ SSL certificate renewed successfully!"
echo ""
echo "Verify with:"
echo "  curl -I https://api.travelwithghost.com/"
echo "  echo | openssl s_client -servername api.travelwithghost.com -connect api.travelwithghost.com:443 2>/dev/null | openssl x509 -noout -dates"
