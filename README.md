# TheBot - Professional Telegram Mux Bot

A powerful Telegram bot designed for video processing, muxing, and file management with professional terminal interface.

## Features

- **Terminal Access**: Execute shell commands directly through Telegram
- **Media Processing**: Advanced video muxing with mkvmerge, ffmpeg
- **File Management**: Upload/download files with Google Drive integration
- **Media Information**: Detailed media analysis with mediainfo
- **Authorization System**: Secure user and group access control
- **Professional Interface**: Clean, minimal design with inline keyboards

## Installed Tools

- **mkvmerge** (mkvtoolnix) - Video muxing and processing
- **ffmpeg** - Video/audio encoding and conversion
- **mediainfo** - Media file analysis
- **mp4decrypt** (Bento4) - DRM content decryption
- **rclone** - Cloud storage integration
- **aria2** - Advanced download manager
- **rar/unrar** - Archive extraction
- **p7zip** - 7-Zip archive support
- **Google Chrome + ChromeDriver** - Web automation
- **fdkaac** - AAC audio encoder
- **wget/curl** - File downloading

## Commands

### Basic Commands
- `/start` - Start the bot and view main menu
- `/help` - Show command reference
- `/settings` - Bot configuration panel

### Terminal Commands
- `/term <command>` - Execute shell command
- `/ls [path]` - List directory contents

### Media Tools
- `/mi <file>` - Show media information (reply to file or provide path)
- `/mux` - Video muxing operations menu
- `/extract <file> [type]` - Extract video/audio/subtitle streams
- `/decrypt <file> <key>` - Decrypt DRM protected content

### File Management
- `/gup <file>` - Upload file to Google Drive
- `/dl <url/magnet>` - Download with aria2 (torrents, HTTP, magnets)
- `/wget <url>` - Simple HTTP download
- `/aclear` - Clear all aria2 downloads
- `/acancel <gid>` - Cancel specific download
- `/ashow` - Show active downloads

### Administration (Owner Only)
- `/auth <user_id>` - Authorize user
- `/unauth <user_id>` - Remove user authorization
- `/authlist` - View authorized users and groups

## Setup

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository_url>
cd TheBot
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Edit `.env` file with your configuration:
```bash
nano .env
```

4. Start with Docker Compose:
```bash
docker-compose up -d
```

### Manual Installation

1. Install Python 3.11.9
2. Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg mediainfo mkvtoolnix rclone wget curl git

# Install mp4decrypt manually
wget https://www.bento4.com/downloads/Bento4-SDK-1-6-0-639.x86_64-unknown-linux.zip
unzip Bento4-SDK-*.zip
sudo cp Bento4-SDK-*/bin/mp4decrypt /usr/local/bin/
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables and run:
```bash
python main.py
```

## Configuration

### Required Environment Variables

- `BOT_TOKEN` - Telegram bot token from @BotFather
- `API_ID` - Telegram API ID from my.telegram.org
- `API_HASH` - Telegram API hash from my.telegram.org
- `OWNER_ID` - Your Telegram user ID
- `DATABASE_URL` - MongoDB connection string

### Optional Environment Variables

- `RCLONE_CONFIG` - Rclone configuration for Google Drive
- `GDRIVE_FOLDER_ID` - Google Drive folder ID for uploads
- `DOWNLOAD_PATH` - Download directory path (default: ./downloads/)
- `TEMP_PATH` - Temporary files path (default: ./temp/)
- `LOG_PATH` - Log files path (default: ./logs/)
- `MAX_FILE_SIZE` - Maximum file size in bytes (default: 2GB)
- `WORKERS` - Number of worker threads (default: 4)
- `COMMAND_TIMEOUT` - Command execution timeout in seconds (default: 300)

## Google Drive Setup

1. Install and configure rclone:
```bash
rclone config
```

2. Create a remote named "gdrive" for Google Drive
3. Set the `RCLONE_CONFIG` environment variable with your config
4. Set `GDRIVE_FOLDER_ID` with your target folder ID

## Security Features

- **Authorization System**: Only authorized users can access the bot
- **Command Filtering**: Dangerous commands are automatically blocked
- **Owner-Only Commands**: Administrative functions restricted to owner
- **Secure File Handling**: Temporary files are automatically cleaned up

## Architecture

```
TheBot/
├── main.py              # Main application entry point
├── config.py            # Configuration management
├── database.py          # Database operations
├── utils.py             # Utility functions
├── handlers/            # Command handlers
│   ├── __init__.py
│   ├── start.py         # Start and help commands
│   ├── terminal.py      # Terminal commands (/term, /ls)
│   ├── files.py         # File operations (/mi, /gup, /download)
│   ├── auth.py          # Authorization commands
│   └── settings.py      # Settings and callbacks
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, contact the bot administrator.