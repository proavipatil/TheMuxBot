# MuxBot

Professional Telegram mux bot for video processing with terminal access and media tools.

## Features

- **Terminal Access**: Execute system commands with real-time output
- **Media Processing**: Video muxing with mkvtoolnix and ffmpeg
- **Download Manager**: aria2 integration for torrents, magnets, and HTTP downloads
- **Media Information**: Detailed media analysis with ffprobe
- **File Management**: Upload, download, and organize files
- **Authorization System**: Owner-only commands with user/group management
- **Google Drive Integration**: Upload files to Google Drive using rclone
- **Professional Interface**: Clean, minimal design with inline keyboards

## Commands

### General
- `/start` - Start the bot and show welcome message
- `/help` - Show available commands

### Terminal & System
- `/term <command>` - Execute terminal command with real-time output
- `/ls [path]` - List directory contents

### Media Processing
- `/mi <file/url>` - Get detailed media information using ffprobe

### Authorization (Owner Only)
- `/auth` - Manage authorized users and groups
- `/auth add user <user_id>` - Add authorized user
- `/auth add group <group_id>` - Add authorized group
- `/auth remove user <user_id>` - Remove authorized user
- `/auth remove group <group_id>` - Remove authorized group
- `/auth list` - List all authorized entities

### Settings (Owner Only)
- `/settings` - Bot configuration and system information
- `/config` - Show current bot configuration

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/proavipatil/TheMuxBot.git
cd TheMuxBot/TheBot
```

2. Copy environment file and configure:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

### Manual Installation

1. Install Python 3.11.9 and required system packages:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3-pip ffmpeg mkvtoolnix mediainfo aria2 rclone

# Install Python dependencies
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Run the bot:
```bash
python main.py
```

## Environment Variables

### Required
- `API_ID` - Your Telegram API ID from my.telegram.org
- `API_HASH` - Your Telegram API Hash from my.telegram.org
- `BOT_TOKEN` - Your Bot Token from @BotFather
- `OWNER_ID` - Your Telegram User ID (owner of the bot)

### Optional
- `MONGO_URI` - MongoDB connection URI for persistent storage
- `TELEGRAPH_TOKEN` - Telegraph API token for media reports
- `DOWNLOAD_PATH` - Download directory (default: downloads)
- `TEMP_PATH` - Temporary files directory (default: temp)
- `WORKERS` - Number of worker threads (default: 4)

## Getting Credentials

### Telegram API
1. Go to [my.telegram.org](https://my.telegram.org)
2. Login with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Copy `API_ID` and `API_HASH`

### Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token

### Your User ID
1. Message @userinfobot on Telegram
2. Copy your user ID

## System Requirements

- Python 3.11.9+
- FFmpeg (for media processing)
- mkvtoolnix (for video muxing)
- mediainfo (for media analysis)
- aria2 (for downloads)
- rclone (for cloud storage)

## Security Features

- Owner-only sensitive commands
- User and group authorization system
- Command validation and sanitization
- Dangerous command blocking
- Secure environment variable handling

## Tech Stack

- **Python 3.11.9** - Programming language
- **Pyrogram** - Telegram MTProto API framework
- **MongoDB** - Database for persistent storage
- **Docker** - Containerization
- **FFmpeg** - Media processing
- **mkvtoolnix** - Video muxing
- **aria2** - Download manager
- **rclone** - Cloud storage integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and updates, join our Telegram channel: [@MuxBotSupport](https://t.me/MuxBotSupport)

## Disclaimer

This bot is for educational and personal use only. Users are responsible for complying with their local laws and Telegram's Terms of Service.