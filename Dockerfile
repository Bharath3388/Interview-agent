FROM python:3.11-slim

# System deps for audio processing + DB
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Railway injects PORT env var; default 8000
EXPOSE 8000
CMD ["python", "-c", "import os; port=os.environ.get('PORT','8000'); import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=int(port))"]
