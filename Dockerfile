FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Expose port
EXPOSE 8000

CMD ["gunicorn", "transactions.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "60", "--workers", "2", "--worker-class", "sync", "--max-requests", "1000", "--max-requests-jitter", "100"]