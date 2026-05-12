FROM python:3.11.9-slim

WORKDIR /app

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

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "school.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "120"]