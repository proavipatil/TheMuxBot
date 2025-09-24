# Use Python 3.11.9 image
FROM python:3.11.9

# Set working directory
WORKDIR /app/

# Install basic dependencies
RUN apt -qq update && apt -qq install -y --no-install-recommends \
    curl git pv jq gnupg2 unzip wget ffmpeg \
    mediainfo aria2 p7zip-full unrar-free rclone

# Add mkvtoolnix
RUN wget -q -O - https://mkvtoolnix.download/gpg-pub-moritzbunkus.txt | apt-key add - && \
    wget -qO - https://ftp-master.debian.org/keys/archive-key-10.asc | apt-key add -
RUN sh -c 'echo "deb https://mkvtoolnix.download/debian/ bullseye main" >> /etc/apt/sources.list.d/bunkus.org.list' && \
    sh -c 'echo deb http://deb.debian.org/debian bullseye main contrib non-free | tee -a /etc/apt/sources.list'
RUN wget -O /usr/share/keyrings/gpg-pub-moritzbunkus.gpg https://mkvtoolnix.download/gpg-pub-moritzbunkus.gpg && \
    apt update && apt install mkvtoolnix mkvtoolnix-gui -y
RUN apt install fdkaac -y

# Install Chrome
RUN mkdir -p /tmp/ && \
    cd /tmp/ && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i ./google-chrome-stable_current_amd64.deb; apt -fqqy install && \
    rm ./google-chrome-stable_current_amd64.deb

# Install ChromeDriver
RUN mkdir -p /tmp/ && \
    cd /tmp/ && \
    wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip chromedriver -d /usr/bin/ && \
    rm /tmp/chromedriver.zip

ENV GOOGLE_CHROME_DRIVER /usr/bin/chromedriver
ENV GOOGLE_CHROME_BIN /usr/bin/google-chrome-stable

# Install RAR
RUN mkdir -p /tmp/ && \
    cd /tmp/ && \
    wget -O /tmp/rarlinux.tar.gz http://www.rarlab.com/rar/rarlinux-x64-6.0.0.tar.gz && \
    tar -xzvf rarlinux.tar.gz && \
    cd rar && \
    cp -v rar unrar /usr/bin/ && \
    rm -rf /tmp/rar*

# Install mp4decrypt (Bento4)
RUN mkdir -p /tmp/ && \
    cd /tmp/ && \
    wget -O /tmp/bento4.zip https://www.bento4.com/downloads/Bento4-SDK-1-6-0-639.x86_64-unknown-linux.zip && \
    unzip /tmp/bento4.zip -d /tmp/ && \
    cp /tmp/Bento4-SDK-*/bin/mp4decrypt /usr/local/bin/ && \
    chmod +x /usr/local/bin/mp4decrypt && \
    rm -rf /tmp/bento4.zip /tmp/Bento4-SDK-*

# Create necessary directories
RUN mkdir -p /app/downloads /app/temp /app/logs

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Run the bot
CMD ["python", "main.py"]