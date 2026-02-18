# syntax=docker/dockerfile:1
FROM python:3.12-slim

# System packages needed for bcrypt and Pillow (photo handling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory (will be replaced by a mounted persistent volume)
RUN mkdir -p data/fault_photos

EXPOSE 8501

# Streamlit reads .streamlit/config.toml automatically
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
