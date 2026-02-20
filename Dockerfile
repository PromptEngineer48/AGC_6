FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY youtube_pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + Chromium
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy project
COPY . .

# Create data directories
RUN mkdir -p output cache temp

# Default port for REST API
EXPOSE 8000

# Default: show help; override CMD to run pipeline
CMD ["python", "-m", "youtube_pipeline.main", "--help"]
