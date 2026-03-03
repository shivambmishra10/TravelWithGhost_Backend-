# Deployment Guide — TravelWithGhost Backend

## Architecture

- **Nginx** → Reverse proxy with SSL termination (ports 80/443)
- **Certbot** → Let's Encrypt SSL certificate management (auto-renews every 12h)
- **Backend** → Django app on port 8000 (internal)
- **PostgreSQL** → Database

## SSL Certificate

Certificates are managed by **Certbot (Let's Encrypt)** and stored in `./nginx/certbot/conf/`.

### Auto-Renewal (built-in)

The `certbot` container automatically attempts renewal **every 12 hours**. The `nginx` container reloads its config **every 6 hours** to pick up new certs. No action needed — this is handled by `docker-compose.prod.yml`.

### Manual Renewal (if cert has expired)

SSH into the AWS instance and run:

```bash
ssh -i <your-key.pem> ubuntu@13.200.20.177
cd /path/to/project
./renew-ssl.sh
```

### First-Time Setup

```bash
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh
```

### Verify Certificate

```bash
echo | openssl s_client -servername api.travelwithghost.com \
  -connect api.travelwithghost.com:443 2>/dev/null | openssl x509 -noout -dates
```

## Deploying Changes

```bash
ssh -i <your-key.pem> ubuntu@13.200.20.177
cd /path/to/project
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

## Useful Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Check running containers
docker-compose -f docker-compose.prod.yml ps

# Check nginx specifically
docker-compose -f docker-compose.prod.yml logs nginx
```
