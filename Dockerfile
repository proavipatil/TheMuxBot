FROM python:3.11.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    mkvtoolnix \
    mediainfo \
    aria2 \
    rclone \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .

# Create necessary directories
RUN mkdir -p downloads temp logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "main.py"]