# Building TravelWithGhost: Docker & AWS Deployment

## Part 4: From Development to Production - DevOps Deep Dive

*How I containerized the entire stack and deployed to AWS EC2*

---

## Introductionz

We've covered architecture, backend, and frontend. Now comes the exciting part: **deployment**! This is where theory meets reality, and where I encountered the most real-world problems (see Part 5).

In this post, I'll explain:
- Docker containerization strategy
- Docker Compose orchestration
- AWS EC2 setup
- Nginx reverse proxy
- SSL certificate automation
- Environment management

---

## Why Docker?

### The Problem Without Docker

**Development**: "Works on my machine! 🎉"
**Production**: "500 Internal Server Error 💀"

**Common Issues**:
- Different Python versions
- Missing system dependencies
- Database connection differences
- File permission issues
- Port conflicts

### The Docker Solution

```
Development:          Production:
┌─────────────┐      ┌─────────────┐
│  Container  │ ───▶ │  Container  │
│  Python 3.13│      │  Python 3.13│
│  Django 5.1 │      │  Django 5.1 │
│  PostgreSQL │      │  PostgreSQL │
└─────────────┘      └─────────────┘
   IDENTICAL            IDENTICAL
```

**Benefits**:
✅ Same environment everywhere
✅ Easy to replicate
✅ Isolated from host system
✅ Version-controlled infrastructure
✅ Simple rollbacks

---

## Docker Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  AWS EC2 Server                  │
│  ┌───────────────────────────────────────────┐  │
│  │          Docker Compose Network            │  │
│  │                                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │  Nginx   │  │ Backend  │  │   DB     │ │  │
│  │  │  :80,:443│  │  :8000   │  │  :5432   │ │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘ │  │
│  │       │             │              │        │  │
│  │       └─────────────┴──────────────┘        │  │
│  │                                             │  │
│  │  ┌──────────┐                               │  │
│  │  │ Certbot  │  (SSL renewal)                │  │
│  │  └──────────┘                               │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## File Structure

```
TravelWithGhost_Backend/
├── docker-compose.dev.yml      # Development
├── docker-compose.prod.yml     # Production
├── init-letsencrypt.sh         # SSL setup script
├── switch-env.sh               # Environment switcher
│
├── backend/
│   ├── Dockerfile              # Backend image definition
│   ├── entrypoint.sh           # Startup script
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (not in git)
│   └── manage.py
│
└── nginx/
    ├── nginx.conf              # Reverse proxy config
    └── certbot/                # SSL certificates
```

---

## Backend Dockerfile

**backend/Dockerfile**:
```dockerfile
# Start from Python 3.13 (Alpine is smaller)
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
```

**Key Decisions**:

1. **`python:3.13-slim`**: Smaller image (150MB vs 1GB)
2. **`PYTHONUNBUFFERED=1`**: Logs appear immediately
3. **System dependencies**: PostgreSQL client, compiler
4. **No `COPY . .` before pip**: Cache layer optimization
5. **Entrypoint script**: Wait for DB before starting

---

## Entrypoint Script

**backend/entrypoint.sh**:
```bash
#!/bin/sh

# Exit on error
set -e

echo "Waiting for PostgreSQL..."

# Wait for database to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "postgres" -d "travelwithghost" -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing command"

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput --clear

# Start Gunicorn
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class gthread \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

**What This Does**:
1. **Waits for PostgreSQL** (prevents connection errors)
2. **Runs migrations** (updates database schema)
3. **Collects static files** (CSS, JS, admin files)
4. **Starts Gunicorn** (production WSGI server)

**Gunicorn Configuration**:
- `--workers 3`: 3 processes (2 × CPU cores + 1)
- `--threads 2`: 2 threads per worker
- `--timeout 60`: 60-second request timeout
- `--bind 0.0.0.0:8000`: Listen on all interfaces

---

## Docker Compose - Development

**docker-compose.dev.yml**:
```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    container_name: travelwithghost_db_dev
    environment:
      POSTGRES_DB: travelwithghost
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: devpassword123
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - app-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: travelwithghost_backend_dev
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
      - media_files_dev:/app/media
      - static_files_dev:/app/staticfiles
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    depends_on:
      - db
    networks:
      - app-network

volumes:
  postgres_data_dev:
  media_files_dev:
  static_files_dev:

networks:
  app-network:
    driver: bridge
```

**Key Features**:
- **Hot reload**: `./backend:/app` mounts code
- **Django dev server**: `runserver` (not Gunicorn)
- **Exposed ports**: Access from host machine
- **Named volumes**: Data persists between restarts

**Commands**:
```bash
# Start development
docker-compose -f docker-compose.dev.yml up

# Rebuild after dependency changes
docker-compose -f docker-compose.dev.yml up --build

# Stop
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes
docker-compose -f docker-compose.dev.yml down -v
```

---

## Docker Compose - Production

**docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    container_name: travelwithghost_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: travelwithghost
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: travelwithghost_backend
    restart: unless-stopped
    volumes:
      - media_files:/app/media
      - static_files:/app/staticfiles
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/admin/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: travelwithghost_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certbot/conf:/etc/letsencrypt:ro
      - ./nginx/certbot/www:/var/www/certbot:ro
      - media_files:/app/media:ro
      - static_files:/app/staticfiles:ro
    depends_on:
      - backend
    networks:
      - app-network
    command: "/bin/sh -c 'while :; do sleep 6h & wait $${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

  certbot:
    image: certbot/certbot
    container_name: travelwithghost_certbot
    restart: unless-stopped
    volumes:
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:
  media_files:
  static_files:

networks:
  app-network:
    driver: bridge
```

**Key Differences from Dev**:

1. **`restart: unless-stopped`**: Auto-restart on crash
2. **Health checks**: Ensure services are actually working
3. **No exposed backend port**: Only Nginx is public
4. **No code mounting**: Code is baked into image
5. **Environment variables**: From `.env` file
6. **Nginx + Certbot**: SSL certificate management

---

## Nginx Configuration

**nginx/nginx.conf**:
```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # Upstream backend
    upstream backend {
        server backend:8000;
    }

    # HTTP server (redirect to HTTPS)
    server {
        listen 80;
        server_name api.travelwithghost.com;

        # Let's Encrypt challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect all other traffic to HTTPS
        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name api.travelwithghost.com;

        # SSL certificates
        ssl_certificate /etc/letsencrypt/live/api.travelwithghost.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/api.travelwithghost.com/privkey.pem;

        # SSL configuration (Mozilla Intermediate)
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Max upload size
        client_max_body_size 10M;

        # API proxy
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Admin proxy
        location /admin/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /app/media/;
            expires 7d;
            add_header Cache-Control "public";
            add_header Access-Control-Allow-Origin "*";
        }
    }
}
```

**Key Features**:

1. **HTTP → HTTPS redirect**: Force secure connections
2. **Let's Encrypt support**: `.well-known/acme-challenge/`
3. **Reverse proxy**: Forward `/api/` to backend container
4. **Static file serving**: Nginx serves files directly
5. **CORS headers**: Allow frontend to fetch images
6. **Rate limiting**: 10 requests/second per IP
7. **Gzip compression**: Reduce bandwidth
8. **Security headers**: HSTS, XSS protection
9. **SSL configuration**: Modern, secure settings

---

## SSL Certificate Setup

**init-letsencrypt.sh**:
```bash
#!/bin/bash

# Configuration
domains=(api.travelwithghost.com)
rsa_key_size=4096
data_path="./nginx/certbot"
email="your-email@example.com"
staging=0  # Set to 1 if testing

# Check if certificates already exist
if [ -d "$data_path/conf/live/${domains[0]}" ]; then
  read -p "Existing data found. Continue and replace? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

# Download recommended TLS parameters
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

# Create dummy certificate
echo "### Creating dummy certificate for ${domains[0]}..."
path="/etc/letsencrypt/live/${domains[0]}"
mkdir -p "$data_path/conf/live/${domains[0]}"
docker-compose -f docker-compose.prod.yml run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

# Start nginx
echo "### Starting nginx..."
docker-compose -f docker-compose.prod.yml up --force-recreate -d nginx
echo

# Delete dummy certificate
echo "### Deleting dummy certificate for ${domains[0]}..."
docker-compose -f docker-compose.prod.yml run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/${domains[0]} && \
  rm -Rf /etc/letsencrypt/archive/${domains[0]} && \
  rm -Rf /etc/letsencrypt/renewal/${domains[0]}.conf" certbot
echo

# Request real certificate
echo "### Requesting Let's Encrypt certificate for ${domains[0]}..."
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Select staging or production
case "$staging" in
  1) staging_arg="--staging" ;;
  *) staging_arg="" ;;
esac

docker-compose -f docker-compose.prod.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $domain_args \
    --email $email \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

# Reload nginx
echo "### Reloading nginx..."
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

**What This Script Does**:
1. Creates dummy certificate (so Nginx can start)
2. Starts Nginx
3. Requests real certificate from Let's Encrypt
4. Replaces dummy with real certificate
5. Reloads Nginx

**Usage**:
```bash
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh
```

---

## Environment Variables

**backend/.env**:
```bash
# Database
DATABASE_URL=postgresql://postgres:TwGh2025PgAdmin@db:5432/travelwithghost
POSTGRES_PASSWORD=TwGh2025PgAdmin

# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=api.travelwithghost.com,localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=https://travelwithghost.com,http://localhost:3000

# Media
MEDIA_URL=/media/
MEDIA_ROOT=/app/media
```

**Security Notes**:
- ⚠️ **Never commit .env to Git** (add to `.gitignore`)
- 🔑 Use strong passwords (20+ characters)
- 🔄 Rotate secrets regularly
- 📦 Use different secrets for dev/prod

**Generate Secret Key**:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## AWS EC2 Setup

### 1. **Launch EC2 Instance**

**Specifications**:
- **AMI**: Ubuntu 22.04 LTS
- **Instance Type**: t2.micro (1 vCPU, 1GB RAM)
- **Storage**: 20GB EBS
- **Security Group**:
  - Port 22 (SSH)
  - Port 80 (HTTP)
  - Port 443 (HTTPS)

### 2. **Connect to Instance**

```bash
# Save your .pem file
chmod 400 travelWithGhostPair.pem

# Connect via SSH
ssh -i travelWithGhostPair.pem ubuntu@65.1.128.230
```

### 3. **Install Docker**

```bash
# Update packages
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (no need for sudo)
sudo usermod -aG docker $USER

# Log out and back in for group to take effect
exit
# SSH back in

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 4. **Clone Repository**

```bash
# Clone your repo
git clone https://github.com/yourusername/TravelWithGhost_Backend.git
cd TravelWithGhost_Backend

# Create .env file
nano backend/.env
# Paste your environment variables

# Make scripts executable
chmod +x backend/entrypoint.sh
chmod +x init-letsencrypt.sh
```

### 5. **Configure Domain**

**DNS Records** (in your domain registrar):
```
Type    Name    Value               TTL
A       api     65.1.128.230        300
```

**Verify**:
```bash
nslookup api.travelwithghost.com
# Should return: 65.1.128.230
```

### 6. **Deploy**

```bash
# Build and start containers
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Setup SSL
./init-letsencrypt.sh
```

---

## Deployment Commands

### **Start Services**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### **Stop Services**
```bash
docker-compose -f docker-compose.prod.yml down
```

### **View Logs**
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 50 lines
docker-compose -f docker-compose.prod.yml logs --tail=50 backend
```

### **Rebuild After Code Changes**
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### **Run Django Commands**
```bash
# Migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Django shell
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell
```

### **Database Backup**
```bash
# Backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres travelwithghost > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres travelwithghost < backup.sql
```

### **Clean Up**
```bash
# Remove stopped containers
docker-compose -f docker-compose.prod.yml rm

# Remove unused images
docker image prune

# Remove unused volumes (⚠️ deletes data)
docker volume prune
```

---

## Environment Switching

**switch-env.sh**:
```bash
#!/bin/bash

ENV=$1

if [ "$ENV" == "dev" ]; then
    echo "Switching to development..."
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.dev.yml up -d
elif [ "$ENV" == "prod" ]; then
    echo "Switching to production..."
    docker-compose -f docker-compose.dev.yml down
    docker-compose -f docker-compose.prod.yml up -d
else
    echo "Usage: ./switch-env.sh [dev|prod]"
fi
```

**Usage**:
```bash
chmod +x switch-env.sh
./switch-env.sh dev   # Switch to development
./switch-env.sh prod  # Switch to production
```

---

## Monitoring & Maintenance

### **Health Checks**

```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# Check container health
docker-compose -f docker-compose.prod.yml ps | grep -E "healthy|unhealthy"

# Test API
curl https://api.travelwithghost.com/api/cities/

# Test SSL
curl -vI https://api.travelwithghost.com
```

### **Resource Usage**

```bash
# Container stats (CPU, RAM)
docker stats

# Disk usage
docker system df

# Detailed disk usage
docker system df -v
```

### **Log Rotation**

Docker automatically rotates logs, but you can configure:

**daemon.json** (`/etc/docker/daemon.json`):
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

---

## Continuous Deployment

### **GitHub Actions Workflow**

**.github/workflows/deploy.yml**:
```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Deploy to AWS EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.AWS_HOST }}
          username: ubuntu
          key: ${{ secrets.AWS_SSH_KEY }}
          script: |
            cd ~/TravelWithGhost_Backend
            git pull origin main
            docker-compose -f docker-compose.prod.yml up -d --build
```

**Setup**:
1. Go to GitHub repo → Settings → Secrets
2. Add `AWS_HOST`: `65.1.128.230`
3. Add `AWS_SSH_KEY`: Contents of `travelWithGhostPair.pem`

Now every push to `main` automatically deploys!

---

## Troubleshooting Commands

### **Container Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check if port is in use
sudo lsof -i :8000

# Restart container
docker-compose -f docker-compose.prod.yml restart backend
```

### **Database Connection Error**
```bash
# Check if db is running
docker-compose -f docker-compose.prod.yml ps db

# Connect to database
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d travelwithghost

# Test from backend
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell
```

### **502 Bad Gateway (Nginx)**
```bash
# Check if backend is running
docker-compose -f docker-compose.prod.yml ps backend

# Test backend directly
docker-compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/admin/

# Check nginx config
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### **SSL Certificate Issues**
```bash
# Check certificate expiry
docker-compose -f docker-compose.prod.yml exec certbot certbot certificates

# Manually renew
docker-compose -f docker-compose.prod.yml exec certbot certbot renew

# Force renewal
docker-compose -f docker-compose.prod.yml exec certbot certbot renew --force-renewal
```

---

## Performance Optimization

### 1. **Docker Image Optimization**

**Before** (1.2GB):
```dockerfile
FROM python:3.13
COPY . .
RUN pip install -r requirements.txt
```

**After** (180MB):
```dockerfile
FROM python:3.13-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

**Improvements**:
- Use `-slim` images
- Copy requirements first (layer caching)
- Use `--no-cache-dir`
- Multi-stage builds for compiled assets

### 2. **PostgreSQL Tuning**

Add to `docker-compose.prod.yml`:
```yaml
db:
  command: postgres -c shared_buffers=256MB -c max_connections=200
```

### 3. **Nginx Caching**

Add to `nginx.conf`:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 10m;
    add_header X-Cache-Status $upstream_cache_status;
}
```

---

## Security Checklist

- ✅ **Firewall configured** (only 22, 80, 443)
- ✅ **SSH key authentication** (no passwords)
- ✅ **SSL/TLS enabled** (HTTPS only)
- ✅ **Environment variables** (not hardcoded)
- ✅ **Django DEBUG=False**
- ✅ **Strong database password**
- ✅ **Rate limiting** (Nginx)
- ✅ **CORS configured** (specific origins)
- ✅ **Security headers** (HSTS, CSP)
- ✅ **Regular updates** (docker images, packages)

---

## Cost Breakdown

**AWS EC2 (t2.micro)**:
- Instance: $8.35/month (free tier eligible)
- Storage (20GB): $2/month
- Data transfer: ~$1/month
**Total**: ~$11/month (or free for 12 months)

**Vercel (Frontend)**:
- Free tier: $0/month

**Domain**:
- .com domain: ~$12/year

**Total Annual Cost**: ~$144/year ($0 with free tiers)

---

## Scaling Considerations

### **Current Setup** (100 users):
```
EC2 t2.micro (1 CPU, 1GB RAM)
└── Good for up to ~100 concurrent users
```

### **Next Steps** (1,000 users):
```
EC2 t2.small (1 CPU, 2GB RAM) + RDS PostgreSQL
└── Good for ~1,000 concurrent users
```

### **Future** (10,000+ users):
```
Load Balancer
├── EC2 Auto Scaling Group (3+ instances)
├── RDS Multi-AZ PostgreSQL
├── ElastiCache Redis
├── S3 for media files
└── CloudFront CDN
```

---

## Key Takeaways

1. **Docker ensures consistency** across environments
2. **Docker Compose orchestrates** multiple services
3. **Nginx is a powerful reverse proxy** and static file server
4. **Let's Encrypt provides free SSL** certificates
5. **Health checks prevent** incomplete deployments
6. **Environment variables keep secrets safe**
7. **Monitoring is essential** for production

---

## What's Next?

In **Part 5** (Real Problems & Solutions), I'll share:
- 7 actual problems I faced during deployment
- Step-by-step debugging process
- How I fixed each issue
- Lessons learned

---

**Coming up: Part 5 - Real Problems & Solutions**

*Questions about Docker or deployment? Drop a comment!*
