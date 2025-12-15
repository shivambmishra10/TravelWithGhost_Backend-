# TravelWithGhost: Complete Deployment Guide

## Part 4: From Local Development to Production

*A practical guide to deploying a full-stack application with real costs and decisions*

---

## What We'll Cover

1. **Local Development** → Run frontend + backend on your machine
2. **Frontend Deployment** → Deploy Next.js to Vercel
3. **Backend Deployment** → Deploy Django to AWS EC2 with Docker
4. **Domain & DNS Setup** → Connect everything together

---

## Phase 1: Local Development Setup

### Backend Setup

The backend repository includes a `switch-env.sh` script that handles environment switching between development and production.

```bash
# Clone backend
git clone https://github.com/shivambmishra10/TravelWithGhost_Backend-.git
cd TravelWithGhost_Backend-

# Make script executable and switch to dev
chmod +x switch-env.sh
./switch-env.sh dev
```

**What `switch-env.sh dev` does:**
- Copies `.env.development` → `.env` (sets local database credentials)
- Starts PostgreSQL in Docker (`docker-compose.dev.yml`)
- Prepares the development environment

```bash
# Now start the Django server
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend running at: `http://localhost:8000`

### Frontend Setup

The frontend is in a **separate repository** — this separation allows independent deployments and keeps concerns isolated.

```bash
# Clone frontend (different repo!)
git clone https://github.com/shivambmishra10/TravelWithGhost.git
cd TravelWithGhost

# Install and run
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Frontend running at: `http://localhost:3000`

---

## Phase 2: Frontend Deployment (Vercel)

### Why Vercel for Frontend?

| Consideration | Vercel | Self-hosted |
|---------------|--------|-------------|
| Setup time | 5 minutes | Hours |
| SSL certificate | Automatic | Manual (Certbot) |
| Global CDN | Included | Extra cost |
| Cost | Free tier | Server cost |

Vercel is built by the Next.js team — zero configuration needed.

### Deployment Steps

1. Go to [vercel.com](https://vercel.com) → Sign in with GitHub
2. Import repository: `TravelWithGhost`
3. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL = https://api.travelwithghost.com
   ```
4. Deploy

Every `git push` to main branch auto-deploys.

---

## Phase 3: Domain Setup

### Domain Purchase

| Item | Cost |
|------|------|
| Domain (travelwithghost.com) | ~₹1800/year |
| GoDaddy purchase | One-time |

### Step 1: Point Domain to Vercel (in GoDaddy)

First, in **GoDaddy DNS settings**, point the entire domain to Vercel:

| Type | Name | Value |
|------|------|-------|
| CNAME | @ | cname.vercel-dns.com |
| CNAME | www | cname.vercel-dns.com |

This tells the internet: "travelwithghost.com → Vercel servers"

### Step 2: Add Domain in Vercel

In **Vercel Dashboard → Project → Settings → Domains**:
- Add `travelwithghost.com`
- Vercel verifies ownership and issues SSL automatically

**Result**: `https://travelwithghost.com` → Frontend ✅

### Step 3: Add API Subdomain (in Vercel Domains)

Still in **Vercel's domain settings** (not GoDaddy), add the API subdomain:

| Type | Name | Value |
|------|------|-------|
| A | api | YOUR_EC2_PUBLIC_IP |

**Why in Vercel, not GoDaddy?**
- Since we pointed the whole domain to Vercel in Step 1, Vercel now manages all subdomains
- Easier to manage everything in one place

**Result**: `https://api.travelwithghost.com` → EC2 Backend ✅

### Complete DNS Flow

```
User types: travelwithghost.com
     │
     ▼
GoDaddy DNS: "Go ask Vercel"
     │
     ▼
Vercel: "Here's the frontend!"
     
─────────────────────────────────

User types: api.travelwithghost.com
     │
     ▼
GoDaddy DNS: "Go ask Vercel"
     │
     ▼
Vercel DNS: "A record points to 13.200.x.x (EC2)"
     │
     ▼
AWS EC2: "Here's the API!"
```

---

## Phase 4: AWS EC2 Setup

### Why t3.small Instead of Free Tier (t2.micro)?

| Instance | RAM | What Happens |
|----------|-----|--------------|
| t2.micro | 1GB | Docker build fails with "out of memory" |
| t3.small | 2GB | Runs smoothly |

**Our stack requires ~1.5GB RAM:**
- PostgreSQL: ~400MB
- Django + Gunicorn: ~300MB
- Nginx: ~50MB
- Docker overhead: ~200MB
- Build process: ~500MB (temporary)

### Cost Reality

| Resource | Cost | Notes |
|----------|------|-------|
| AWS Credits | $100 (started) → $88 (remaining) | ~3 months left |
| t3.small | ~$15/month | After credits: real cost |
| Domain | ~₹1800/year | ~₹150/month |

### SSH Setup

```bash
# Save your .pem key securely
mv ~/Downloads/travelwithghost-key.pem ~/.ssh/
chmod 400 ~/.ssh/travelwithghost-key.pem

# Add alias to ~/.zshrc for quick access
alias twg="ssh -i ~/.ssh/travelwithghost-key.pem ubuntu@<YOUR_EC2_IP>"
```

Now just type `twg` to connect.

### Install Docker

```bash
# On EC2 server
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
logout  # Re-login for group to take effect
```

---

## Phase 5: Understanding Docker Architecture

### Why Not One Big Container?

Many beginners think Docker = one container with everything. That's wrong.

```
❌ WRONG: One Container
┌─────────────────────────────────┐
│  Django + PostgreSQL + Nginx    │
│  If Django crashes → DB down    │
│  If DB needs update → All down  │
└─────────────────────────────────┘

✅ CORRECT: Separate Containers
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Django  │  │ Postgres │  │  Nginx   │
│  :8000   │  │  :5432   │  │  :80/443 │
└──────────┘  └──────────┘  └──────────┘
     │              │              │
     └──────────────┴──────────────┘
           Docker Network
```

**Benefits of separation:**
- **Isolation**: Backend crash ≠ Database crash
- **Independent updates**: Upgrade PostgreSQL without touching Django
- **Scaling**: Run 3 backend containers, 1 database
- **Security**: Each container has minimal permissions

### Docker Volumes: Why Both Containers Mount the Same Folder

**The Core Problem**: Containers are sandboxed — they can't see the host filesystem or each other's files.

```
┌─────────────────────────────────────────────────────────────────┐
│                     EC2 SERVER HARD DISK                         │
│                                                                  │
│   /var/lib/docker/volumes/media_files/_data/                    │
│   └── photo.jpg   ← Actual file lives HERE (on host disk)       │
│                                                                  │
│           ▲                           ▲                         │
│           │                           │                         │
│       MOUNT (window)              MOUNT (window)                │
│           │                           │                         │
│   ┌───────┴───────┐           ┌───────┴───────┐                │
│   │    Backend    │           │     Nginx     │                │
│   │   Container   │           │   Container   │                │
│   │               │           │               │                │
│   │ Sees: /app/   │           │ Sees: /var/   │                │
│   │       media/  │           │   www/media/  │                │
│   │               │           │               │                │
│   │  Can WRITE ✏️  │           │  Can READ 👁️   │                │
│   └───────────────┘           └───────────────┘                │
│                                                                  │
│           Both "windows" point to the SAME folder!              │
└─────────────────────────────────────────────────────────────────┘
```

**Think of it like this**: A volume is a USB drive plugged into both containers. Backend writes files, Nginx reads them, but the actual data lives on the host disk.

### What Happens When Container Dies?

| Action | Files Deleted? |
|--------|----------------|
| Container stops/crashes | ❌ No — files are on host disk |
| Container removed | ❌ No — volume is separate from container |
| `docker-compose down` | ❌ No — volumes persist |
| `docker-compose down -v` | ✅ **YES** — `-v` flag removes volumes |

**Key insight**: The container only has a "window" into the folder. Window closes = container dies. But the folder (and files) remain on the host disk.

### Why Not Let Django Serve Files Directly?

| Approach | Speed | Why |
|----------|-------|-----|
| Django serves files | 🐢 Slow | Python reads file → processes → sends |
| Nginx serves files | 🚀 Fast | C-based, optimized for static files |

With shared volumes: Django writes, Nginx serves — best of both worlds.

### Container Communication

Containers talk via **Docker's internal DNS**, not localhost:

```python
# In Django settings
DATABASE_URL = "postgresql://postgres:password@db:5432/travelwithghost"
#                                              ^^
#                            "db" = PostgreSQL container name
#                            Docker resolves this to container's IP
```

```nginx
# In nginx.conf
upstream backend {
    server backend:8000;  # "backend" = Django container name
}
```

---

## Phase 6: Production Deployment

### Clone and Configure

```bash
# On EC2 server
git clone https://github.com/shivambmishra10/TravelWithGhost_Backend-.git
cd TravelWithGhost_Backend-

# Create production environment
nano backend/.env.production
```

```env
DEBUG=False
SECRET_KEY=generate-a-random-secret-key-here
DATABASE_URL=postgresql://postgres:YourStrongPassword@db:5432/travelwithghost
ALLOWED_HOSTS=api.travelwithghost.com
CORS_ALLOWED_ORIGINS=https://travelwithghost.com
CSRF_TRUSTED_ORIGINS=https://travelwithghost.com
```

### Start Production Stack

```bash
# Copy production env
cp backend/.env.production backend/.env

# Build and start all containers
docker-compose -f docker-compose.prod.yml up -d --build
```

**What happens:**

```
docker-compose.prod.yml
         │
         ├── db (PostgreSQL)
         │   └── Image: postgres:15 (downloaded from Docker Hub)
         │   └── Volume: postgres_data (persistent)
         │
         ├── backend (Django)
         │   └── Built from: backend/Dockerfile
         │   └── Runs: entrypoint.sh (waits for DB → migrates → starts Gunicorn)
         │   └── Volumes: media_files, static_files
         │
         ├── nginx (Reverse Proxy)
         │   └── Image: nginx:alpine
         │   └── Config: nginx/nginx.conf
         │   └── Volumes: media_files (read-only), static_files (read-only)
         │
         └── certbot (SSL)
             └── Renews certificates every 12 hours
```

### SSL Certificate Setup

```bash
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh
```

This script:
1. Creates dummy certificates (so Nginx can start)
2. Starts Nginx
3. Requests real certificates from Let's Encrypt
4. Replaces dummy with real certificates
5. Reloads Nginx

---

## Final Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
 travelwithghost.com                   api.travelwithghost.com
        │                                       │
        ▼                                       ▼
┌───────────────┐                     ┌─────────────────────────┐
│    VERCEL     │                     │       AWS EC2           │
│   (Frontend)  │                     │  ┌─────────────────┐    │
│               │ ──── API Calls ───▶ │  │     Nginx       │    │
│   Next.js     │                     │  │  (SSL + Proxy)  │    │
│   React       │                     │  └────────┬────────┘    │
│   Global CDN  │                     │           │             │
└───────────────┘                     │  ┌────────▼────────┐    │
                                      │  │     Django      │    │
                                      │  │   (Gunicorn)    │    │
                                      │  └────────┬────────┘    │
                                      │           │             │
                                      │  ┌────────▼────────┐    │
                                      │  │   PostgreSQL    │    │
                                      │  └─────────────────┘    │
                                      │                         │
                                      │  ┌─────────────────┐    │
                                      │  │ Docker Volumes  │    │
                                      │  │ • media_files   │    │
                                      │  │ • static_files  │    │
                                      │  │ • postgres_data │    │
                                      │  └─────────────────┘    │
                                      └─────────────────────────┘
```

---

## Essential Commands Reference

### Logs & Debugging
```bash
docker-compose -f docker-compose.prod.yml logs -f           # All logs
docker-compose -f docker-compose.prod.yml logs -f backend   # Backend only
docker exec -it travelwithghost_backend bash                # Shell into container
```

### Restart & Rebuild
```bash
docker-compose -f docker-compose.prod.yml restart backend   # Restart service
docker-compose -f docker-compose.prod.yml up -d --build     # Rebuild all
```

### Database
```bash
# Access PostgreSQL
docker exec -it travelwithghost_db psql -U postgres -d travelwithghost

# Backup
docker exec travelwithghost_db pg_dump -U postgres travelwithghost > backup.sql

# Restore
docker exec -i travelwithghost_db psql -U postgres travelwithghost < backup.sql
```

### Cleanup
```bash
docker system prune -a    # Remove unused images/containers (careful!)
```

---

## Deployment Checklist

- [ ] Backend runs locally (`./switch-env.sh dev`)
- [ ] Frontend runs locally (separate repo)
- [ ] Frontend deployed to Vercel
- [ ] Domain purchased and configured in Vercel
- [ ] EC2 instance running (t3.small)
- [ ] Docker installed on server
- [ ] Production `.env` configured
- [ ] `docker-compose up` successful
- [ ] SSL certificate installed
- [ ] API accessible at `https://api.travelwithghost.com`
- [ ] Frontend can call backend API

---

## Conclusion

This completes the **4-part engineering blog series** for TravelWithGhost:

| Part | Topic |
|------|-------|
| **Part 1** | System Architecture & Design Decisions |
| **Part 2** | Backend Deep Dive (Django, DRF, Models) |
| **Part 3** | Frontend Deep Dive (Next.js, React, Auth) |
| **Part 4** | Docker & Deployment (This post) |

### What We Built

A full-stack travel companion platform with:
- **Frontend**: Next.js on Vercel (global CDN, auto-deploy)
- **Backend**: Django REST API on AWS EC2
- **Database**: PostgreSQL in Docker
- **Infrastructure**: Nginx reverse proxy, SSL via Let's Encrypt
- **Cost**: ~₹1500/month ($15 EC2 + domain)

### Key Takeaways

1. **Separate concerns**: Frontend and backend in different repos, deployed independently
2. **Docker isolation**: Each service in its own container, volumes for persistence
3. **DNS flow matters**: Understand how domains resolve before debugging
4. **Volumes ≠ Containers**: Files live on host disk, containers just have windows to them

---

*Thanks for following along! If you found this series helpful, feel free to star the repos or connect with me.*

**GitHub**: [Frontend](https://github.com/shivambmishra10/TravelWithGhost) | [Backend](https://github.com/shivambmishra10/TravelWithGhost_Backend-)
