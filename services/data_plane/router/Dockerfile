FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/data_plane/router/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY services/shared /app/shared

# Copy service code
COPY services/data_plane/router/main.py .

EXPOSE 8200

CMD ["python", "main.py"]
