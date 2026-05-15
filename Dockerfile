FROM python:3.12-slim

WORKDIR /app

# Build args (needed for collectstatic to run)
ARG SECRET_KEY
ARG DEBUG=False
ARG DATABASE_URL

ENV SECRET_KEY=$SECRET_KEY
ENV DEBUG=$DEBUG
ENV DATABASE_URL=$DATABASE_URL

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    libxml2-dev \
    libxslt1-dev \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "school.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]