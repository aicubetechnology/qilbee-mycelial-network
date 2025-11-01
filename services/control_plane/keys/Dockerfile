FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/control_plane/keys/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY services/shared /app/shared

# Copy service code
COPY services/control_plane/keys/main.py .

EXPOSE 8101

CMD ["python", "main.py"]
