# CHARLI Sidecar — Python ML Worker (STT + TTS)
FROM python:3.11-slim

WORKDIR /app

# Install espeak-ng (TTS fallback) and curl (health check).
RUN apt-get update && \
    apt-get install -y --no-install-recommends espeak-ng curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the sidecar application.
COPY sidecar.py .

EXPOSE 3001

CMD ["python3", "sidecar.py"]
