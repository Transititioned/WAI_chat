FROM python:3.10-slim

WORKDIR /app

# System deps (minimal, safe)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# HF exposes port 7860 automatically
EXPOSE 7860

# Start ASGI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
