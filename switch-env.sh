#!/bin/bash

# Script to switch between development and production environments

function switch_to_dev() {
    echo "Switching to development environment..."
    cd backend
    cp .env.development .env
    cd ..
    echo "Starting development database..."
    docker-compose -f docker-compose.dev.yml up -d
    echo "Development environment is ready!"
    echo "Run 'python manage.py runserver' to start the development server"
}

function switch_to_prod() {
    echo "Switching to production environment..."
    cd backend
    cp .env.production .env
    cd ..
    echo "Production environment is ready!"
    echo "Use 'docker-compose -f docker-compose.prod.yml up -d' to start production services"
}

case "$1" in
    "dev")
        switch_to_dev
        ;;
    "prod")
        switch_to_prod
        ;;
    *)
        echo "Usage: $0 {dev|prod}"
        exit 1
        ;;
esac