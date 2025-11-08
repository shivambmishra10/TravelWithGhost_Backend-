# TravelWithGhost Backend API

A Django-based REST API backend for the TravelWithGhost travel planning platform. This repository contains the backend server, database configuration, and deployment setup.

## Features

- User Authentication & Authorization
- Trip Management & Planning
- City Information & Details
- Media Upload & Management
- Real-time Chat Integration
- Docker Containerization
- Nginx & SSL Configuration

## Tech Stack

- Python 3.13
- Django 5.1.6
- PostgreSQL 13
- Docker & Docker Compose
- Nginx
- Gunicorn

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/shivambmishra10/TravelWithGhost.git
   cd TravelWithGhost/backend
   ```

2. Set up environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.development .env
   ```

4. Run development server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Production Deployment

1. Set up production environment:
   ```bash
   cp .env.production .env
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## API Documentation

- `/api/cities/` - City management endpoints
- `/api/trips/` - Trip management endpoints
- `/api/auth/` - Authentication endpoints
- `/admin/` - Django admin interface

## Environment Variables

Required environment variables:
- `DEBUG` - Debug mode
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection URL
- `ALLOWED_HOSTS` - Allowed hostnames
- `CORS_ALLOWED_ORIGINS` - CORS settings

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request