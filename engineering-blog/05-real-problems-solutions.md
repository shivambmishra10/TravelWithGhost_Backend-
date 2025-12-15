# Building TravelWithGhost: Real Problems & Solutions

## Part 5: Debugging Stories and Lessons Learned

*The messy truth about building in production*

---

## Introduction

Every tutorial makes development look smooth. Reality? It's messy, frustrating, and full of learning. This post documents the **actual problems** I encountered while deploying TravelWithGhost and how I solved them.

---

## Problem 1: The Case of the Missing Images

### The Symptom
```
Frontend deployed ✅
Backend deployed ✅
API working ✅
Images? 404 Not Found ❌
```

### The Investigation

**Step 1**: Check API response
```bash
curl https://api.travelwithghost.com/api/cities/
[{"id":1,"name":"Goa","image":null}]
```

💡 **Discovery**: API returns `null` for image!

**Step 2**: Check database
```python
# Django shell
city = City.objects.get(id=1)
print(city.image)  # Empty!
```

💡 **Discovery**: Database has no image path!

**Step 3**: Check if image file exists
```bash
ls /app/media/
# Only profile_photos/ folder, no Goa.jpg!
```

💡 **Discovery**: Image file doesn't exist in container!

### The Root Cause

**Problem**: Media files were only on my local machine, not on the server!

**Why it happened**:
1. `.gitignore` excludes `media/` folder (correct for security)
2. Docker volume was empty on first build
3. I assumed files would magically appear 🤦

### The Solution

**Step 1**: Upload media files to server
```bash
# Local machine
cd backend
tar -czf media.tar.gz media/
scp -i ~/.ssh/key.pem media.tar.gz ubuntu@server:~/
```

**Step 2**: Extract on server
```bash
# On server
tar -xzf media.tar.gz
```

**Step 3**: Copy to Docker container
```bash
sudo docker cp ~/media/Goa.jpg $(docker-compose ps -q backend):/app/media/
```

**Step 4**: Update database
```python
# Django shell
city = City.objects.get(id=1)
city.image = 'Goa.jpg'
city.save()
```

**Step 5**: Add CORS headers for images
```nginx
location /media/ {
    alias /var/www/media/;
    add_header Access-Control-Allow-Origin "*";
}
```

### Lessons Learned

✅ **Docker volumes don't auto-populate**  
✅ **Media files need manual copying**  
✅ **CORS matters for cross-origin images**  
✅ **Test the entire flow, not just APIs**

---

## Problem 2: PostgreSQL Password Authentication Failed

### The Symptom
```
backend_1  | Waiting for PostgreSQL to be ready...
backend_1  | Waiting for PostgreSQL to be ready...
backend_1  | Waiting for PostgreSQL to be ready...
db_1       | FATAL: password authentication failed for user "postgres"
```

### The Investigation

**The error logs**:
```
db_1 | Password does not match for user "postgres"
db_1 | Connection matched pg_hba.conf line 99: "host all all all md5"
```

**Check environment variables**:
```bash
cat backend/.env
DATABASE_URL=postgresql://postgres:TwGh2025PgAdmin@db:5432/travelwithghost
POSTGRES_PASSWORD=TwGh2025PgAdmin
```

Looks correct! 🤔

**Check entrypoint.sh**:
```bash
while ! python -c "import psycopg2; psycopg2.connect(
    host='db', 
    dbname='${POSTGRES_DB}', 
    user='${POSTGRES_USER}', 
    password='${POSTGRES_PASSWORD}'
)" 2>/dev/null; do
    sleep 1
done
```

Uses environment variables... but are they defined? 🤔

### The Root Cause

**Problem 1**: Old PostgreSQL data had different password!
```
db_1 | PostgreSQL Database directory appears to contain a database; 
db_1 | Skipping initialization
```

**Problem 2**: Environment variables in `entrypoint.sh` weren't set!
- `.env` file loads for Django
- But shell script doesn't see them

### The Solution

**Step 1**: Remove old PostgreSQL data
```bash
docker-compose down -v  # -v removes volumes
```

**Step 2**: Fix entrypoint.sh to use hardcoded credentials
```bash
#!/bin/sh
echo "Waiting for PostgreSQL to be ready..."
while ! python -c "import psycopg2; psycopg2.connect(
    host='db', 
    dbname='travelwithghost', 
    user='postgres', 
    password='TwGh2025PgAdmin'
)" 2>/dev/null; do
    sleep 1
done
```

**Step 3**: Rebuild and restart
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Lessons Learned

✅ **Docker volumes persist data** (even passwords!)  
✅ **Shell scripts need explicit variable passing**  
✅ **Always check if database is fresh or reused**  
✅ **`docker-compose down -v` is your friend**

---

## Problem 3: Images Loading Locally But Not in Production

### The Symptom
```
Local: Images ✅
Production: Images ❌ (broken image icon)
```

### The Investigation

**Check image URL in production**:
```javascript
// Frontend code
src={`http://localhost:8000${city.image}`}
```

😱 **Hardcoded localhost!**

**Browser console**:
```
Failed to load resource: net::ERR_CONNECTION_REFUSED
http://localhost:8000/media/Goa.jpg
```

### The Root Cause

**Problem**: Hardcoded `localhost:8000` in frontend code

**Why it worked locally**:
- Frontend: `localhost:3000`
- Backend: `localhost:8000`
- Same machine, so `localhost` works!

**Why it failed in production**:
- Frontend: Vercel CDN
- Backend: AWS EC2
- Different machines, `localhost` refers to user's machine!

### The Solution

**Step 1**: Use environment variable
```javascript
// Before
src={`http://localhost:8000${city.image}`}

// After
src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${city.image}`}
```

**Step 2**: Create `.env.production`
```bash
NEXT_PUBLIC_API_URL=https://api.travelwithghost.com
```

**Step 3**: Set in Vercel
```
Vercel Dashboard → Settings → Environment Variables
Name: NEXT_PUBLIC_API_URL
Value: https://api.travelwithghost.com
```

**Step 4**: Update Next.js config
```javascript
// next.config.mjs
images: {
  domains: ['api.travelwithghost.com', 'localhost'],
  remotePatterns: [
    {
      protocol: 'https',
      hostname: 'api.travelwithghost.com',
      pathname: '/media/**',
    },
  ],
}
```

### Lessons Learned

✅ **Never hardcode URLs**  
✅ **Environment variables are essential**  
✅ **Test in production-like environment**  
✅ **Clear browser cache when testing**

---

## Problem 4: Nginx Serving 404 for Media Files

### The Symptom
```bash
curl https://api.travelwithghost.com/media/Goa.jpg
HTTP/1.1 404 Not Found
```

But the file exists in the container! 🤔

### The Investigation

**Check container**:
```bash
docker exec backend ls -la /app/media/
# Goa.jpg is there!
```

**Check nginx**:
```bash
docker exec nginx ls -la /var/www/media/
# Empty! 😱
```

### The Root Cause

**Problem**: Nginx and backend don't share the same volume!

**docker-compose.yml**:
```yaml
backend:
  volumes:
    - media_files:/app/media

nginx:
  volumes:
    - media_files:/var/www/media
```

Both reference `media_files` volume, but it's empty!

**Why?**: Volume was created empty, and backend built without copying media files.

### The Solution

**Step 1**: Copy files to backend container
```bash
docker cp ~/media/. $(docker-compose ps -q backend):/app/media/
```

**Step 2**: Verify nginx sees them
```bash
docker exec nginx ls -la /var/www/media/
# Files appear! ✅
```

**Step 3**: Test URL
```bash
curl -I https://api.travelwithghost.com/media/Goa.jpg
HTTP/1.1 200 OK
```

### Lessons Learned

✅ **Docker volumes are shared storage**  
✅ **Both containers see the same files**  
✅ **Named volumes persist between restarts**  
✅ **Copy files to ANY container using the volume**

---

## Problem 5: SSL Certificate Issues

### The Symptom
```
http://api.travelwithghost.com ✅
https://api.travelwithghost.com ❌
```

### The Investigation

**Check certbot logs**:
```bash
docker-compose logs certbot
# Certificate doesn't exist!
```

**Check nginx config**:
```nginx
ssl_certificate /etc/letsencrypt/live/api.travelwithghost.com/fullchain.pem;
# File doesn't exist yet!
```

### The Root Cause

**Chicken-and-egg problem**:
1. Nginx needs certificates to start HTTPS
2. Certbot needs Nginx running to verify domain
3. But Nginx can't start without certificates! 🐔🥚

### The Solution

**Use the init-letsencrypt.sh script**:

```bash
#!/bin/bash

# Download recommended TLS parameters
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > nginx/certbot/conf/options-ssl-nginx.conf
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > nginx/certbot/conf/ssl-dhparams.pem

# Start nginx
docker-compose up -d nginx

# Request certificate
docker-compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d api.travelwithghost.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Reload nginx
docker-compose exec nginx nginx -s reload
```

**Step by step**:
1. Start nginx WITHOUT SSL first
2. Get certificate via HTTP-01 challenge
3. Reload nginx with SSL enabled

### Lessons Learned

✅ **SSL setup has ordering requirements**  
✅ **Let's Encrypt needs HTTP access first**  
✅ **Use init scripts for multi-step setups**  
✅ **Automate certificate renewal with cron**

---

## Problem 6: Frontend Not Using Production API

### The Symptom
```
Vercel deployed ✅
Backend working ✅
Frontend shows no data ❌
```

### The Investigation

**Check browser console**:
```
GET http://localhost:8000/api/cities/ net::ERR_CONNECTION_REFUSED
```

Still using localhost! 😱

**Check Vercel environment variables**:
```
# Empty! 
```

### The Root Cause

**Problem**: Environment variable not set in Vercel!

**Why?**: 
- Local `.env.production` file exists
- But Vercel doesn't automatically read it
- Need to manually set in Vercel dashboard

### The Solution

**Step 1**: Set in Vercel
```
Dashboard → Settings → Environment Variables
NEXT_PUBLIC_API_URL = https://api.travelwithghost.com
Environment: Production, Preview, Development
```

**Step 2**: Redeploy
```
Dashboard → Deployments → Latest → Redeploy
```

**Step 3**: Verify
```bash
# Check in browser console
console.log(process.env.NEXT_PUBLIC_API_URL)
// https://api.travelwithghost.com ✅
```

### Lessons Learned

✅ **Vercel needs manual env var setup**  
✅ **Must redeploy after changing env vars**  
✅ **Test with browser DevTools**  
✅ **Document all required env vars**

---

## Problem 7: CORS Errors After Deployment

### The Symptom
```
Browser console:
Access to fetch at 'https://api.travelwithghost.com/api/cities/' 
from origin 'https://travelwithghost.com' has been blocked by CORS policy
```

### The Investigation

**Check Django settings**:
```python
CORS_ALLOWED_ORIGINS = [
    'https://travelwithghost.com',
    'https://www.travelwithghost.com'
]
```

Looks correct! But Vercel gave me a different URL:
```
https://travelwithghost-xyz123.vercel.app
```

### The Root Cause

**Problem**: Vercel preview deployments have random URLs!

**Why it failed**:
- Preview: `https://travelwithghost-abc123.vercel.app`
- Production: `https://travelwithghost.com`
- Only production URL in CORS whitelist!

### The Solution

**Option 1**: Add all Vercel URLs
```python
CORS_ALLOWED_ORIGINS = [
    'https://travelwithghost.com',
    'https://www.travelwithghost.com',
    'https://travelwithghost.vercel.app',
    'https://travelwithghost-*.vercel.app',  # Won't work!
]
```

**Option 2**: Use custom domain only
```python
# Only allow production domain
CORS_ALLOWED_ORIGINS = [
    'https://travelwithghost.com',
]
```

**Option 3**: Regex pattern (development)
```python
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://travelwithghost.*\.vercel\.app$",
]
```

### Lessons Learned

✅ **Vercel creates preview URLs for each deployment**  
✅ **CORS must include all frontend URLs**  
✅ **Use regex for dynamic preview URLs**  
✅ **Or restrict to production domain only**

---

## Development vs Production Differences

### Configuration Matrix

| Feature | Development | Production |
|---------|-------------|-----------|
| **Frontend URL** | localhost:3000 | travelwithghost.com |
| **Backend URL** | localhost:8000 | api.travelwithghost.com |
| **Database** | SQLite / Local PostgreSQL | Docker PostgreSQL |
| **Debug Mode** | DEBUG=True | DEBUG=False |
| **HTTPS** | HTTP | HTTPS (Let's Encrypt) |
| **Static Files** | Django serves | Nginx serves |
| **Media Files** | Local folder | Docker volume + Nginx |
| **CORS** | * (allow all) | Specific origins |
| **Secret Key** | Anything | Strong random key |

---

## Debugging Toolkit

### Essential Commands

**Check running containers**:
```bash
docker-compose ps
```

**View logs**:
```bash
docker-compose logs -f backend
docker-compose logs -f nginx
docker-compose logs -f db
```

**Access container shell**:
```bash
docker-compose exec backend sh
docker-compose exec nginx sh
```

**Check files in container**:
```bash
docker-compose exec backend ls -la /app/media/
docker-compose exec nginx ls -la /var/www/media/
```

**Test API directly**:
```bash
curl -I https://api.travelwithghost.com/api/cities/
curl https://api.travelwithghost.com/media/Goa.jpg
```

**Check SSL certificate**:
```bash
openssl s_client -connect api.travelwithghost.com:443 -servername api.travelwithghost.com
```

**Django shell**:
```bash
docker-compose exec backend python manage.py shell
```

---

## Preventive Measures

### 1. **Checklist for Deployment**

```markdown
Backend:
- [ ] .env file created on server
- [ ] Database credentials correct
- [ ] Media files uploaded
- [ ] Docker volumes created
- [ ] Nginx CORS headers set
- [ ] SSL certificate obtained
- [ ] Django collectstatic run

Frontend:
- [ ] Environment variables set in Vercel
- [ ] API URL points to production
- [ ] Build successful
- [ ] No hardcoded URLs

Testing:
- [ ] API responds
- [ ] Images load
- [ ] Authentication works
- [ ] CORS no errors
- [ ] HTTPS works
```

### 2. **Documentation**

Create a `DEPLOYMENT.md`:
```markdown
# Deployment Guide

## Prerequisites
- AWS EC2 instance
- Domain name
- Vercel account

## Backend Setup
1. Clone repo
2. Create .env file
3. Run docker-compose up

## Frontend Setup
1. Connect to Vercel
2. Set environment variables
3. Deploy

## Common Issues
- Images 404: Copy media files
- Password error: Reset DB volume
- CORS error: Check origins
```

### 3. **Environment Templates**

Create `.env.example`:
```bash
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:5432/db
ALLOWED_HOSTS=api.example.com,localhost
CORS_ALLOWED_ORIGINS=https://example.com
```

---

## Conclusion: What I Learned

### Technical Lessons

1. **Docker is not magic** - understand volumes, networks, and containers
2. **Environment matters** - what works locally may fail in production
3. **CORS is critical** - plan cross-origin communication from the start
4. **Debugging is systematic** - check logs, test incrementally
5. **Documentation saves time** - future you will thank present you

### Soft Skills

1. **Google is your friend** - but understand what you're copying
2. **Break down problems** - tackle one issue at a time
3. **Ask for help** - community is supportive
4. **Document everything** - you'll forget in a week
5. **Celebrate small wins** - deployment is hard!

### Tools That Helped

- **curl** - test APIs directly
- **docker logs** - see what's happening
- **browser DevTools** - inspect network requests
- **Django shell** - debug database issues
- **Git** - rollback when things break

---

## Final Thoughts

Building TravelWithGhost taught me that:

> **Perfect code doesn't exist. Working code in production does.**

Every error was a learning opportunity. Every bug fixed made me a better developer. And now, the app is live, serving real users!

---

**The entire blog series**:
- Part 1: System Architecture
- Part 2: Backend Deep Dive
- Part 3: Frontend Deep Dive
- Part 4: Docker & Deployment
- Part 5: Real Problems & Solutions (this post)

---

*What's your biggest deployment horror story? Share in the comments!*

*GitHub: [TravelWithGhost Frontend](https://github.com/shivambmishra10/TravelWithGhost) | [TravelWithGhost Backend](https://github.com/shivambmishra10/TravelWithGhost_Backend-)*
