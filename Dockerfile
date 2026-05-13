FROM python:3.11.9-slim

WORKDIR /app

ARG DEBUG
ARG SECRET_KEY
ARG DATABASE_URL

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    pkg-config \
    libpq-dev \
    libfreetype6 \
    libfreetype6-dev \
    libjpeg-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libpng-dev \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --upgrade setuptools && \
    python -c "import pkg_resources; print('pkg_resources OK')"

COPY . .

RUN DATABASE_URL=${DATABASE_URL} python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["uvicorn", "school.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "120"]