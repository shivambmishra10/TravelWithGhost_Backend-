# TravelWithGhost Production Deployment Guide

## Current Deployment Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     PRODUCTION ENVIRONMENT                      │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vercel)                        │
│  Domain: https://travelwithghost.com                            │
│  • Auto-deploys on git push                                     │
│  • Global CDN included                                          │
│  • Auto SSL certificate                                         │
│  Env: NEXT_PUBLIC_API_URL=https://api.travelwithghost.com      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                        HTTPS Request
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AWS EC2 VM (13.200.20.177)                   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         Docker Compose (docker-compose.prod.yml)         │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  Nginx (Port 80/443)                                │ │ │
│  │  │  • SSL/TLS Termination                              │ │ │
│  │  │  • Reverse Proxy                                    │ │ │
│  │  │  • Static & Media File Serving                      │ │ │
│  │  │  • Let's Encrypt Certificates                       │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                     ↓                                      │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  Backend (Django + Gunicorn, Port 8000)             │ │ │
│  │  │  • Django REST API                                  │ │ │
│  │  │  • Business Logic                                   │ │ │
│  │  │  • Media Uploads                                    │ │ │
│  │  │  • Auto-runs migrations on startup                  │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                     ↓                                      │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  PostgreSQL Database (Port 5432)                    │ │ │
│  │  │  • Data Persistence                                 │ │ │
│  │  │  • User, Trip, Chat Data                            │ │ │
│  │  │  • Auto-healthcheck                                 │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Volumes:                                                        │
│  • postgres_data → DB persistence                              │
│  • static_files → Django static assets                         │
│  • media_files → User uploads (profile photos, etc)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Files for Production

### 1. **docker-compose.prod.yml** (Orchestration)
- Defines all services: backend, db, nginx, certbot
- Volume mappings for data persistence
- Network configuration
- Environment file: `backend/.env`

### 2. **backend/Dockerfile** (Container Image)
- Python 3.13 slim image
- Installs dependencies from `requirements.txt`
- Runs `collectstatic` for static files
- Sets up Gunicorn WSGI server
- Runs `entrypoint.sh` on startup

### 3. **backend/entrypoint.sh** (Startup Script)
```bash
# 1. Waits for PostgreSQL to be ready
# 2. Runs: python manage.py migrate
# 3. Starts Gunicorn with 3 workers
```

### 4. **nginx/nginx.conf** (Reverse Proxy)
- HTTP (port 80) → Redirects to HTTPS
- HTTPS (port 443) with Let's Encrypt certificates
- Serves static files from `/var/www/static/`
- Serves media files from `/var/www/media/`
- Proxies `/api/` requests to backend:8000

### 5. **backend/.env** (Production Secrets)
```
DATABASE_URL=postgresql://postgres:TwGh2025PgAdmin@db:5432/travelwithghost
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=api.travelwithghost.com,13.200.20.177
SECURE_SSL_REDIRECT=True
```

---

## Deployment Workflow

### Step 1: Connect to AWS VM

```bash
# SSH into your VM
ssh -i your-key.pem ec2-user@13.200.20.177

# Or if using ubuntu:
ssh -i your-key.pem ubuntu@13.200.20.177
```

### Step 2: Clone Repository on VM

```bash
cd /home/ec2-user  # or your chosen directory
git clone https://github.com/shivambmishra10/TravelWithGhost_Backend-.git
cd TravelWithGhost_Backend-
```

### Step 3: Prepare Production Environment

```bash
# Switch to production environment
chmod +x switch-env.sh
./switch-env.sh prod

# This copies .env.production → backend/.env
```

### Step 4: Initial Setup (First Time Only)

```bash
# Get SSL certificates from Let's Encrypt
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh

# This:
# 1. Creates certbot directories
# 2. Starts nginx temporarily
# 3. Gets SSL cert for api.travelwithghost.com
# 4. Reloads nginx
```

### Step 5: Start Production Containers

```bash
# Pull latest code (if already cloned)
git pull origin main

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

---

## Deploying Your Changes (Budget Feature)

### Changes Made:
✅ Backend: Added `budget` field to Trip model  
✅ Migration: Created 0004_trip_budget.py  
✅ Serializers: Updated to include `budget` in responses  
✅ Frontend: Added budget input in create form  
✅ Frontend: Display budget in trip details  
✅ Changed currency from USD to INR  

### Deployment Steps:

#### 1. **Push Changes to Git**

```bash
cd /Users/shivammishra/Desktop/circulus
git add -A
git commit -m "feat: Add budget field to trips with INR currency"
git push origin main
```

#### 2. **Pull Changes on AWS VM**

```bash
ssh -i your-key.pem ec2-user@13.200.20.177

cd /path/to/TravelWithGhost_Backend-
git pull origin main
```

#### 3. **Rebuild Backend Docker Image**

```bash
# Stop current containers
docker-compose -f docker-compose.prod.yml down

# Rebuild the backend image (will pick up new requirements.txt if needed)
docker-compose -f docker-compose.prod.yml build

# Start all services again
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. **Verify Database Migration Ran**

```bash
# Check logs to ensure migration applied
docker-compose -f docker-compose.prod.yml logs backend

# You should see: "Applying trips.0004_trip_budget..."
```

#### 5. **Update Frontend on Vercel** (if needed)

```bash
# Since frontend is on Vercel, just push to GitHub:
cd frontend
git add -A
git commit -m "feat: Add budget field display with INR currency"
git push origin main

# Vercel auto-deploys when you push to main
# Check deployment status at https://vercel.com
```

---

## Monitoring & Verification

### Check if Changes are Live

```bash
# 1. Check API response includes budget field
curl -H "Authorization: Token YOUR_TOKEN" \
  https://api.travelwithghost.com/api/trips/

# Should include "budget": "15000.00" in response
```

### View Container Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Just backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Just database
docker-compose -f docker-compose.prod.yml logs -f db

# Just nginx
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Check Docker Status

```bash
# List running containers
docker-compose -f docker-compose.prod.yml ps

# Example output:
# NAME                  STATUS
# backend               Up 2 hours
# db                    Up 2 hours
# nginx                 Up 2 hours
```

---

## Common Troubleshooting

### Migrations Not Running?

```bash
# Manually run migrations
docker-compose -f docker-compose.prod.yml exec backend \
  python manage.py migrate

# Check migration status
docker-compose -f docker-compose.prod.yml exec backend \
  python manage.py showmigrations trips
```

### Database Connection Issues?

```bash
# Check database health
docker-compose -f docker-compose.prod.yml exec db \
  pg_isready -U postgres

# Check container logs
docker-compose -f docker-compose.prod.yml logs db
```

### Nginx Not Proxying Correctly?

```bash
# Check nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Static Files Not Loading?

```bash
# Regenerate static files
docker-compose -f docker-compose.prod.yml exec backend \
  python manage.py collectstatic --noinput

# Restart nginx to serve new files
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## Quick Reference Commands

```bash
# SSH into VM
ssh -i key.pem ec2-user@13.200.20.177

# Navigate to project
cd /path/to/TravelWithGhost_Backend-

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Run command in backend container
docker-compose -f docker-compose.prod.yml exec backend python manage.py [command]

# Access database inside container
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d travelwithghost
```

---

## SSL Certificate Renewal (Annual)

The Let's Encrypt certificate lasts 90 days but auto-renews via the certbot service.

```bash
# Manual renewal if needed
docker-compose -f docker-compose.prod.yml run --rm certbot renew
```

---

## Summary

Your production setup is fully containerized with:
- **Nginx**: Reverse proxy + SSL + static files
- **Django**: REST API + business logic
- **PostgreSQL**: Data persistence
- **Let's Encrypt**: Free SSL certificates
- **Gunicorn**: Production WSGI server

All changes are deployed via:
1. Git push to main branch
2. Pull on AWS VM
3. Docker rebuild
4. Restart containers
