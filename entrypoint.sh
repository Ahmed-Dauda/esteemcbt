version: '3.8'

services:
  web:
    build: .
    image: ${IMAGE_NAME}
    # NO ports section - this fixes your deployment error!
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-school.settings.production}
      - DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS}
      - DEBUG=${DEBUG:-False}
    volumes:
      - media_data:/app/media
      - static_data:/app/staticfiles
    restart: unless-stopped

volumes:
  media_data:
  static_data: