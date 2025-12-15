# Building TravelWithGhost: A Full-Stack Travel Companion Platform

## Part 1: System Architecture & Design Decisions

*A journey through building a modern web application from scratch*

---

## Introduction

TravelWithGhost is a full-stack web application that connects travelers looking to explore destinations together. In this blog series, I'll take you through the entire architecture, design decisions, challenges, and solutions I encountered while building this platform.

### What Does TravelWithGhost Do?

- **Destination Discovery**: Browse popular travel destinations
- **Trip Creation**: Users can create and host group trips
- **Social Features**: Join trips, connect with travelers
- **Real-time Communication**: Chat with trip members
- **Profile Management**: User profiles with photos and preferences

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                         │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Next.js Frontend (Vercel)                   │   │
│  │  • React Components                                   │   │
│  │  • Client-side Routing                                │   │
│  │  • State Management                                   │   │
│  │  • Bootstrap UI                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                      REVERSE PROXY LAYER                     │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Nginx (Docker Container)                 │   │
│  │  • SSL/TLS Termination                                │   │
│  │  • Static File Serving                                │   │
│  │  • Load Balancing                                     │   │
│  │  • CORS Headers                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        Django REST API (Docker Container)             │   │
│  │  • REST API Endpoints                                 │   │
│  │  • Token Authentication                               │   │
│  │  • Business Logic                                     │   │
│  │  • Image Processing                                   │   │
│  │  • Gunicorn WSGI Server                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                         │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         PostgreSQL (Docker Container)                 │   │
│  │  • Relational Data Storage                            │   │
│  │  • ACID Compliance                                    │   │
│  │  • Data Persistence                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Docker Container Architecture (Backend on AWS EC2)

**Key Concept**: Each service runs in its **own isolated container**, not one big container.

```
┌─────────────────────────────────────────────────────────────┐
│  AWS EC2 Server (Host Machine)                               │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container 1: backend                                 │   │
│  │  - Django 5.1.6 + Gunicorn                           │   │
│  │  - Python 3.13                                        │   │
│  │  - Port: 8000                                         │   │
│  │  - Mounts: /app/media, /app/staticfiles             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container 2: db                                      │   │
│  │  - PostgreSQL 13                                      │   │
│  │  - Port: 5432                                         │   │
│  │  - Mounts: /var/lib/postgresql/data                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container 3: nginx                                   │   │
│  │  - Nginx Alpine                                       │   │
│  │  - Ports: 80, 443                                     │   │
│  │  - Mounts: /var/www/media, /var/www/static          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container 4: certbot                                 │   │
│  │  - Let's Encrypt SSL Tool                            │   │
│  │  - Runs every 12h for renewal                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Docker Volumes (Persistent Storage on Host)         │   │
│  │  Location: /var/lib/docker/volumes/                  │   │
│  │                                                        │   │
│  │  📁 postgres_data/     ← Database files              │   │
│  │  📁 media_files/       ← User uploads (images)       │   │
│  │  📁 static_files/      ← CSS, JS, admin UI           │   │
│  └──────────────────────────────────────────────────────┘   │
│           ↑                    ↑                              │
│           │ (shared volume)    │ (shared volume)             │
│  ┌────────┴────────┐  ┌───────┴──────┐                      │
│  │  Backend        │  │  Nginx        │                      │
│  │  writes files   │  │  reads files  │                      │
│  └─────────────────┘  └───────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**Why Separate Containers?**

1. **Isolation**: Backend crash ≠ Database crash
2. **Scalability**: Scale backend independently
3. **Updates**: Rebuild one container without affecting others
4. **Security**: Each container has minimal permissions
5. **Technology Mix**: Different base images (Python, PostgreSQL, Nginx)

---

## Tech Stack Breakdown

### Frontend
- **Framework**: Next.js 14
- **Language**: JavaScript (React)
- **UI Library**: React Bootstrap
- **Styling**: CSS Modules + Custom CSS
- **HTTP Client**: Axios
- **Deployment**: Vercel

### Backend
- **Framework**: Django 5.1.6
- **Language**: Python 3.13
- **REST API**: Django REST Framework
- **Authentication**: Token-based (DRF)
- **WSGI Server**: Gunicorn
- **Deployment**: Docker on AWS EC2

### Database
- **RDBMS**: PostgreSQL 13
- **ORM**: Django ORM
- **Deployment**: Docker Container

### DevOps & Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx
- **SSL/TLS**: Let's Encrypt (Certbot)
- **Cloud Provider**: AWS EC2
- **Version Control**: Git & GitHub

---

## Key Design Decisions

### 1. **Why Next.js for Frontend?**

**Decision**: Use Next.js instead of Create React App, Vite, or vanilla React

**Alternatives Considered**:
- Create React App (CRA)
- Vite + React
- Vanilla React with custom webpack
- Vue.js / Angular

**Why I Chose Next.js**:

✅ **File-Based Routing**
```
pages/index.js       → /
pages/login.js       → /login
pages/cities/[id].js → /cities/:id
```
No need to configure React Router manually!

✅ **Built-in Optimizations**
- Automatic code splitting per page
- Image optimization (next/image)
- Font optimization
- Fast refresh during development

✅ **SEO-Friendly**
- Server-side rendering capability (if needed later)
- Better for search engines
- Social media preview cards work perfectly

✅ **Vercel Integration**
- Zero-config deployment
- Automatic HTTPS
- Global CDN distribution
- Git push = auto-deploy

✅ **Great Developer Experience**
- Fast refresh
- Clear error messages
- TypeScript support (optional)
- Active community

**Trade-offs**:
- ❌ Learning curve for file-based routing
- ❌ Framework lock-in (Next.js specific)
- ✅ Worth it for the DX and performance gains

---

### 2. **Why Django for Backend?**

**Decision**: Use Django REST Framework instead of Node.js, FastAPI, or Flask

**Alternatives Considered**:
- Express.js (Node.js)
- FastAPI (Python)
- Flask (Python)
- NestJS (Node.js)

**Why I Chose Django**:

✅ **Batteries Included**
- ORM built-in (no need for separate library)
- Admin panel out of the box
- Authentication system ready
- Security features enabled by default

✅ **Django REST Framework**
- Powerful serializers
- Token authentication ready
- Browsable API for debugging
- Great documentation

✅ **ORM Advantages**
```python
# Django ORM - Clean & readable
Trip.objects.filter(destination__name="Goa")

# vs Raw SQL - Error-prone
cursor.execute("SELECT * FROM trips WHERE destination_name = %s", ["Goa"])
```

✅ **Mature Ecosystem**
- 18+ years of development
- Proven at scale (Instagram, Pinterest)
- Huge library ecosystem
- Security updates regular

**Trade-offs**:
- ❌ Heavier than Flask/FastAPI
- ❌ Python can be slower than Node.js
- ✅ But simplicity and features win for this project

---

### 3. **Why PostgreSQL over MySQL/MongoDB?**

**Decision**: Use PostgreSQL instead of MySQL or MongoDB

**Alternatives Considered**:
- MySQL
- MongoDB (NoSQL)
- SQLite (dev only)

**Why I Chose PostgreSQL**:

✅ **Relational Data**
```
Users ←→ Profiles
  ↓
Trips ←→ Cities
  ↓
JoinRequests
  ↓
ChatMessages
```
Data has clear relationships = perfect for SQL

✅ **Advanced Features**
- JSON fields (best of both worlds)
- Full-text search
- Array fields
- Better indexing than MySQL

✅ **Data Integrity**
- ACID compliance
- Foreign key constraints
- Transaction support

✅ **Django Support**
- Best-supported database in Django
- All ORM features work perfectly

**Why NOT MongoDB?**:
- ❌ Trip data is highly relational
- ❌ Join operations would be complex
- ❌ Schema changes easier with SQL migrations

---

### 4. **Why Separate Frontend and Backend Deployments?**

**Decision**: Deploy frontend on Vercel, backend on AWS EC2

**Alternatives Considered**:
- Monolith (Django templates + Django views)
- Both on AWS
- Both on Vercel
- Netlify for frontend

**Why I Chose Separate Deployments**:

✅ **Frontend on Vercel**:
```
User (India) → Edge location (Mumbai) → Fast!
User (USA)   → Edge location (NYC)    → Fast!
```
- Global CDN = Faster page loads worldwide
- Free tier generous (100GB bandwidth)
- Auto-deploy on git push
- Zero configuration needed

✅ **Backend on AWS**:
```
Control over:
├── Docker configuration
├── Environment variables
├── Database backups
├── Server resources
└── Custom scripts
```
- Full control over infrastructure
- Can SSH into server
- Cost-effective (t2.micro free tier)
- Persistent storage for uploads

✅ **Independent Scaling**:
```
Frontend traffic spikes (viral post)
  ↓
Only scale Vercel CDN (automatic)
  ↓
Backend unaffected
```

**Why NOT Monolith?**:
- ❌ Django templates are outdated
- ❌ No SPA (Single Page App) experience
- ❌ Harder to maintain
- ❌ Frontend can't be CDN-distributed

**Trade-offs**:
- ❌ Need to configure CORS
- ❌ Two deployment pipelines
- ✅ But performance and flexibility win

---

### 5. **Why Docker Containerization?**

**Decision**: Use Docker Compose for backend orchestration

**Alternatives Considered**:
- Direct installation on server
- Kubernetes (overkill)
- Heroku (limited control)

**Why I Chose Docker**:

✅ **"Works on My Machine" → Works Everywhere**
```
Development (Mac)      Production (AWS)
└── Same Python 3.13   └── Same Python 3.13
└── Same PostgreSQL 13 └── Same PostgreSQL 13
└── Same dependencies  └── Same dependencies
```

✅ **Isolated Services**
```
Without Docker:
Server
├── Python 3.13 (backend)
├── PostgreSQL 13 (conflicts with Python?)
├── Nginx (needs separate install)
└── Everything mixed up! 😱

With Docker:
Container 1: Backend
Container 2: Database
Container 3: Nginx
Container 4: Certbot
└── Each isolated! ✨
```

✅ **Easy Rollback**
```bash
# Something broke? Roll back!
docker-compose down
git checkout previous-commit
docker-compose up -d
# Back to working state in 30 seconds
```

✅ **Development = Production**
```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production (same structure!)
docker-compose -f docker-compose.prod.yml up
```

**Why 4 Separate Containers?**:

1. **Backend Container** (Django + Gunicorn)
   - Handles API requests
   - Processes business logic
   - Can restart without affecting DB

2. **Database Container** (PostgreSQL)
   - Stores data
   - Runs independently
   - Survives backend crashes

3. **Nginx Container** (Web Server)
   - Handles SSL/HTTPS
   - Serves static files FAST
   - Reverse proxy to backend

4. **Certbot Container** (SSL Tool)
   - Renews certificates automatically
   - Runs every 12 hours
   - No manual SSL management

**Why NOT One Big Container?**:
```
One container:
Backend crash → Database down → Everything down! 💥

Separate containers:
Backend crash → Database still running → Less downtime! ✅
```

---

### 6. **Why Docker Volumes for Media Storage?**

**Decision**: Store user uploads in Docker volumes on AWS, not Vercel

**Why NOT Store Media on Vercel?**:

❌ **Vercel is Read-Only**
```
User uploads photo
  ↓
Vercel: "Error: Filesystem is read-only"
  ↓
Upload fails ❌
```

❌ **Vercel Resets on Deploy**
```
Monday: User uploads 100 photos
Tuesday: Deploy new code
Wednesday: All photos DELETED! 💥
```

❌ **Vercel is for Static Assets**
```
Vercel is great for:
✅ HTML, CSS, JS (built at deploy time)
✅ Next.js pages
✅ Static images in /public/

Vercel is BAD for:
❌ User-generated content
❌ Dynamic file uploads
❌ Files that change after deployment
```

✅ **AWS Docker Volumes = Perfect**:
```
User uploads photo
  ↓
Backend saves to /app/media/photo.jpg
  ↓
Docker volume: media_files (on AWS disk)
  ↓
File persists forever ✅
  ↓
Nginx serves file directly
  ↓
https://api.travelwithghost.com/media/photo.jpg
```

**How Volumes Work**:
```
AWS EC2 Server (Physical Disk)
└── /var/lib/docker/volumes/media_files/_data/
    └── photo.jpg  ← Actual file location
          ↓
    (mounted/shared between containers)
          ↓
    ┌─────┴─────────────┬──────────────┐
    ↓                   ↓              ↓
Backend             Nginx        Survives
/app/media/photo.jpg /var/www/... restarts!
(writes file)       (reads file)
```

**Why This Architecture?**:

1. **Persistence**: Survives container restarts/rebuilds
2. **Shared Access**: Multiple containers access same files
3. **Performance**: Nginx serves files directly (fast!)
4. **Backups**: Easy to backup entire volume

**Complete Flow**:
```
1. User uploads Goa.jpg via frontend
   ↓
2. POST /api/cities/ with multipart/form-data
   ↓
3. Backend saves to media_files volume
   ↓
4. Database stores: {"image": "/media/Goa.jpg"}
   ↓
5. Frontend displays: <img src="https://api.../media/Goa.jpg" />
   ↓
6. Browser requests image from Nginx
   ↓
7. Nginx reads from media_files volume
   ↓
8. Nginx serves file directly (NOT through Django!)
   ↓
9. Fast delivery! ⚡
```

---

### 7. **Why Token-Based Authentication?**

**Decision**: Use Django REST Framework Token Authentication

**Alternatives Considered**:
- Session-based auth (cookies)
- JWT (JSON Web Tokens)
- OAuth2

**Why I Chose DRF Tokens**:

✅ **Stateless**
```
No need to store session on server
Token in header = instant auth
Perfect for REST API
```

✅ **Simple**
```python
# Built into DRF
from rest_framework.authtoken.models import Token

# One line to create
token = Token.objects.create(user=user)
```

✅ **Mobile-Friendly**
```
Mobile app in future?
Just send token in header
No cookie management needed
```

✅ **Secure with HTTPS**
```
Token sent in header
HTTPS encrypts everything
Man-in-the-middle protected
```

**Why NOT Sessions?**:
- ❌ Requires server-side storage
- ❌ Harder for mobile apps
- ❌ CSRF protection complexity

**Why NOT JWT?**:
- ❌ More complex to implement
- ❌ Can't invalidate easily
- ❌ DRF tokens sufficient for this scale

---

### 8. **Why RESTful API Design?**

**Decision**: Pure REST API with clear resource endpoints

**Alternatives Considered**:
- GraphQL
- gRPC
- WebSockets for everything

**Why I Chose REST**:

✅ **Standard & Simple**
```
GET    /api/trips/        # List trips
POST   /api/trips/        # Create trip
GET    /api/trips/5/      # Get trip detail
PUT    /api/trips/5/      # Update trip
DELETE /api/trips/5/      # Delete trip
```
Everyone understands this!

✅ **HTTP Caching**
```
GET /api/cities/
Cache-Control: max-age=3600
↓
Browser caches for 1 hour
↓
Faster subsequent loads
```

✅ **Great Tooling**
```
- Postman for testing
- curl for debugging
- DRF Browsable API
- Browser network tab
```

✅ **Semantic URLs**
```
/api/trips/5/join/     # Clear: Join trip 5
/api/trips/5/chat/     # Clear: Chat for trip 5
/api/profile/          # Clear: My profile
```

**Why NOT GraphQL?**:
- ❌ Overkill for this project
- ❌ More complex frontend code
- ❌ Harder to cache
- ✅ REST is perfect for CRUD operations

---

### 9. **Why Nginx as Reverse Proxy?**

**Decision**: Use Nginx instead of serving directly from Django

**Why I Chose Nginx**:

✅ **Static File Performance**
```
Without Nginx:
User → Django → Read file → Send (SLOW 🐌)

With Nginx:
User → Nginx → Read file → Send (FAST ⚡)
```
Nginx is 10x faster for static files!

✅ **SSL Termination**
```
Nginx handles HTTPS
  ↓
Django only sees HTTP
  ↓
Simpler Django config
```

✅ **Load Balancing** (Future)
```
Nginx
├─→ Backend Container 1
├─→ Backend Container 2
└─→ Backend Container 3
```

✅ **Security Features**
- Rate limiting
- DDoS protection
- Hide backend details

**Why NOT Serve from Django?**:
- ❌ Django is slow for static files
- ❌ Wastes backend resources
- ❌ No SSL optimization
- ❌ Can't handle high traffic

---

## Summary: Architecture Philosophy

**My Approach**:
1. ✅ **Separation of Concerns**: Each service does one thing well
2. ✅ **Use the Right Tool**: Next.js for frontend, Django for backend, PostgreSQL for data
3. ✅ **Developer Experience**: Easy to develop, test, and deploy
4. ✅ **Scalability**: Can scale parts independently
5. ✅ **Simplicity**: Avoid over-engineering (no Kubernetes, no microservices yet)

---

## Network Architecture

### Production Environment

```
Internet (Users Worldwide)
   ↓
DNS: travelwithghost.com → 13.200.20.177
   ↓
AWS EC2 Server (13.200.20.177)
   ↓
┌─────────────────────────────────────────┐
│  Docker Container Network               │
│                                         │
│  Nginx (Ports 80/443)                  │
│    ├─→ /api/*                          │
│    │   └─→ Backend:8000 (Django)      │
│    │                                   │
│    ├─→ /media/*                        │
│    │   └─→ Directly serves from       │
│    │       media_files volume          │
│    │                                   │
│    └─→ /static/*                       │
│        └─→ Directly serves from        │
│            static_files volume         │
│                                         │
│  Backend:8000 (Django + Gunicorn)      │
│    └─→ Connects to db:5432            │
│                                         │
│  Database:5432 (PostgreSQL)            │
│                                         │
└─────────────────────────────────────────┘
   ↓
Docker Volumes (Persistent Storage)
├── postgres_data    → /var/lib/postgresql/data
├── media_files      → /app/media (backend) + /var/www/media (nginx)
└── static_files     → /app/staticfiles (backend) + /var/www/static (nginx)
```

### Development Environment

```
localhost:3000    → Next.js Dev Server (Frontend)
      ↓ API Calls
localhost:8000    → Django Dev Server (Backend)
      ↓
localhost:5432    → PostgreSQL (Docker or Local)
```

### Container Communication

Containers talk to each other via **Docker network** (not localhost):

```
Frontend (Vercel)
   ↓ HTTPS
Nginx Container
   ├─→ http://backend:8000  (Docker DNS)
   └─→ Reads from volumes directly

Backend Container
   └─→ postgresql://db:5432  (Docker DNS)

Database Container
   └─→ Isolated, only backend can access
```

**Why Service Names?**
- Each container has its own `localhost`
- Docker provides internal DNS
- `backend` resolves to backend container's IP
- `db` resolves to database container's IP

---

## Data Flow Examples

### Example 1: Loading Goa Destination Image

Complete flow from user browser to image display:

```
1. User opens homepage
   https://travelwithghost.com
   ↓
2. Frontend fetches cities
   GET https://api.travelwithghost.com/api/cities/
   ↓
3. Request hits AWS EC2 (13.200.20.177:443)
   ↓
4. Nginx container receives request
   ↓
5. Nginx forwards to backend
   GET http://backend:8000/api/cities/
   ↓
6. Django queries PostgreSQL
   SELECT * FROM trips_city;
   ↓
7. PostgreSQL returns data
   [{id: 1, name: "Goa", image: "/media/Goa.jpg"}]
   ↓
8. Django serializes response
   {"id": 1, "name": "Goa", "image": "/media/Goa.jpg"}
   ↓
9. Nginx adds CORS headers and returns to browser
   ↓
10. Frontend renders image tag
    <img src="https://api.travelwithghost.com/media/Goa.jpg" />
    ↓
11. Browser requests image
    GET https://api.travelwithghost.com/media/Goa.jpg
    ↓
12. Nginx receives request, checks config
    location /media/ {
      alias /var/www/media/;  ← Nginx's mount point
    }
    ↓
13. Nginx reads from Docker volume
    Container: /var/www/media/Goa.jpg
       ↓ (mounted from)
    Volume: media_files
       ↓ (stored on)
    Host: /var/lib/docker/volumes/media_files/_data/Goa.jpg
    ↓
14. Nginx serves file directly (908KB, image/jpeg)
    ↓
15. Browser displays image ✅

Total time: ~200ms
```

**Key Points**:
- API request goes through Django
- Image request served DIRECTLY by Nginx (fast!)
- Docker volume shared between backend (write) and nginx (read)

### Example 2: Creating a Trip

Let's trace how data flows through the system:

```
1. User fills trip form in React
   - Group name: "Goa Beach Party"
   - Dates, itinerary, etc.
   ↓
2. Frontend validates input
   - Check required fields
   - Validate date ranges
   ↓
3. POST /api/trips/
   Headers: Authorization: Token abc123xyz
   Body: {group_name: "Goa Beach Party", ...}
   ↓
4. Nginx receives request (Port 443)
   ↓
5. Nginx forwards to Gunicorn
   http://backend:8000/api/trips/
   ↓
6. Django middleware validates token
   - Looks up Token in database
   - Authenticates user
   ↓
7. View receives request
   - Calls TripSerializer.is_valid()
   ↓
8. Serializer validates data
   - Checks all required fields
   - Validates business rules
   ↓
9. View creates Trip + TripItinerary in PostgreSQL
   - INSERT INTO trips_trip ...
   - INSERT INTO trips_tripitinerary ...
   ↓
10. PostgreSQL commits transaction
    ↓
11. Serializer converts to JSON
    {id: 5, group_name: "Goa Beach Party", ...}
    ↓
12. Nginx adds CORS headers
    Access-Control-Allow-Origin: https://travelwithghost.com
    ↓
13. Frontend receives response (201 Created)
    ↓
14. React redirects to trip detail page
    router.push('/trips/5')
    ↓
15. Trip created successfully! ✅
```

### Example 3: User Uploads Profile Photo

```
1. User selects photo in profile form
   ↓
2. Frontend creates FormData
   formData.append('photo', file)
   ↓
3. PUT /api/profile/
   Content-Type: multipart/form-data
   ↓
4. Nginx forwards to backend (increased size limit)
   client_max_body_size 10M;
   ↓
5. Django receives file
   request.FILES['photo']
   ↓
6. Backend saves to media volume
   File path: /app/media/profile_photos/user123.jpg
      ↓ (saved to Docker volume)
   media_files volume
      ↓ (persisted on host)
   /var/lib/docker/volumes/media_files/_data/profile_photos/user123.jpg
   ↓
7. Database updated
   UPDATE trips_profile 
   SET photos = 'profile_photos/user123.jpg'
   WHERE user_id = 123;
   ↓
8. Response: {photos: "/media/profile_photos/user123.jpg"}
   ↓
9. Frontend displays new photo
   <img src="https://api.travelwithghost.com/media/profile_photos/user123.jpg" />
   ↓
10. Future requests: Nginx serves directly from volume
    (no Django involvement)
```

---

## Docker Volume Deep Dive

### What Are Docker Volumes?

Docker volumes are **persistent storage on the host machine** that containers can access.

**Without Volumes** (Bad ❌):
```
Container filesystem
├── /app/media/photo.jpg
└── Container restarts → FILE DELETED 💥
```

**With Volumes** (Good ✅):
```
Host machine disk
├── /var/lib/docker/volumes/media_files/_data/photo.jpg
└── Container restarts → FILE STILL THERE ✅
```

### Volume Architecture

```
AWS EC2 Server (Physical SSD)
└── /var/lib/docker/volumes/
    ├── media_files/
    │   └── _data/
    │       ├── Goa.jpg
    │       └── profile_photos/
    │           └── user123.jpg
    │
    ├── static_files/
    │   └── _data/
    │       ├── admin/css/
    │       └── rest_framework/
    │
    └── postgres_data/
        └── _data/
            └── (PostgreSQL database files)

These volumes are MOUNTED into containers:

Backend Container                 Nginx Container
├── /app/media/          ←────┐   ├── /var/www/media/
├── /app/staticfiles/    ←────┼─→ ├── /var/www/static/
                              │
                    SAME VOLUMES (shared)
```

### Why This Works

1. **Persistence**: Files survive container lifecycle
2. **Sharing**: Multiple containers access same files
3. **Performance**: OS handles filesystem efficiently
4. **Backups**: Easy to backup entire volume
5. **Isolation**: Volumes separate from container images

### docker-compose.yml Configuration

```yaml
services:
  backend:
    volumes:
      - media_files:/app/media          # Write access
      - static_files:/app/staticfiles   # Write access

  nginx:
    volumes:
      - media_files:/var/www/media:ro   # Read-only
      - static_files:/var/www/static:ro # Read-only

  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Read+Write

volumes:
  media_files:      # Named volume (Docker manages location)
  static_files:     # Named volume
  postgres_data:    # Named volume
```

**`:ro` means read-only** - Nginx can't modify files, only serve them.

---

## Security Considerations

### 1. **HTTPS Everywhere**
- Let's Encrypt SSL certificates
- Force HTTPS redirects
- HSTS headers enabled

### 2. **CORS Protection**
```python
CORS_ALLOWED_ORIGINS = [
    'https://travelwithghost.com',
    'https://www.travelwithghost.com'
]
```

### 3. **Authentication**
- Token-based auth
- Password validation
- Secure password hashing (Django defaults)

### 4. **Input Validation**
- Django form validation
- DRF serializers
- Age restrictions on trips
- File upload limits

### 5. **Security Headers**
```nginx
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
```

---

## Performance Optimizations

### 1. **Static File Serving**
- Nginx serves static files directly
- 1-year cache expiry
- gzip compression

### 2. **Media Files**
- Separate media volume
- CORS enabled for cross-origin
- CDN-ready architecture

### 3. **Database Queries**
- Django ORM optimization
- select_related() for ForeignKeys
- Proper indexing on frequent queries

### 4. **Frontend**
- Next.js automatic code splitting
- Image optimization
- Bootstrap tree-shaking

---

## Scalability Considerations

### Current Limitations
- **Single Server**: No horizontal scaling yet
- **Database**: Single PostgreSQL instance
- **File Storage**: Local volume (not distributed)

### Future Improvements
- **Load Balancer**: Add multiple backend instances
- **Database**: PostgreSQL read replicas
- **Media Storage**: Move to S3 or CloudFront
- **Caching**: Add Redis for sessions/cache
- **Message Queue**: Add Celery for async tasks

---

## Development Workflow

### Local Development
```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

### Deployment
```bash
# Frontend (Automatic)
git push origin main  # Auto-deploys to Vercel

# Backend (Manual)
ssh ubuntu@65.1.128.230
cd ~/TravelWithGhost_Backend
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## Monitoring & Maintenance

### Current Setup
- **Logs**: Docker logs
- **Health Checks**: PostgreSQL healthcheck
- **SSL Renewal**: Automatic via Certbot cron

### What's Missing
- Application monitoring (e.g., Sentry)
- Performance metrics
- Uptime monitoring
- Database backups automation

---

## Lessons Learned

### 1. **Environment Variables Are Critical**
Managing `.env` files across environments was tricky. Key learnings:
- Never commit `.env` to git
- Use `.env.example` as template
- Document all required variables

### 2. **Docker Volumes Can Be Confusing**
Media files weren't showing up initially because:
- Volume was empty after rebuild
- Needed to manually copy files
- Named volumes persist data

### 3. **CORS Configuration Takes Time**
Getting frontend-backend communication working required:
- Proper CORS headers in Django
- Nginx CORS configuration
- Environment variable management

### 4. **SSL Setup Isn't Trivial**
Let's Encrypt setup involved:
- Proper DNS configuration
- Certbot container configuration
- Nginx SSL configuration
- Renewal automation

---

## What's Next?

In the upcoming blog posts, I'll dive deeper into:

- **Part 2**: Django backend architecture, models, and API design
- **Part 3**: Next.js frontend structure and React patterns
- **Part 4**: Docker & deployment deep dive
- **Part 5**: Real problems and debugging stories

---

## Repository Structure

```
TravelWithGhost/
├── frontend/                 # Next.js frontend (separate repo)
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/           # Next.js pages
│   │   ├── styles/          # CSS files
│   │   └── utils/           # API client, helpers
│   ├── public/              # Static assets
│   └── package.json
│
└── backend/                  # Django backend (separate repo)
    ├── config/              # Django settings
    ├── trips/               # Main app
    ├── media/               # User uploads
    ├── nginx/               # Nginx config
    ├── docker-compose.prod.yml
    ├── Dockerfile
    └── requirements.txt
```

---

## Conclusion

Building TravelWithGhost taught me the importance of:
- **Architecture Planning**: Think before you code
- **Separation of Concerns**: Keep frontend and backend independent
- **DevOps Matters**: Deployment is part of development
- **Security First**: Build security in, not on
- **Documentation**: Future you will thank present you

In the next post, we'll dive deep into the Django backend architecture and explore how the models, serializers, and views work together.

---

## Questions to Explore in Comments

1. Why did you choose Django over FastAPI or Node.js?
2. How do you handle database migrations in production?
3. What's your backup strategy?
4. Have you considered GraphQL instead of REST?

---

**Stay tuned for Part 2: Django Backend Deep Dive!**

---

*Follow me on Medium for more engineering stories and practical guides.*

*GitHub: [TravelWithGhost Frontend](https://github.com/shivambmishra10/TravelWithGhost) | [TravelWithGhost Backend](https://github.com/shivambmishra10/TravelWithGhost_Backend-)*
