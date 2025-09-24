#!/usr/bin/env python3
"""
Quick start script for TheBot
"""

import os
import sys

def main():
    """Main function to start the bot"""
    print("🤖 Starting TheBot...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📝 Please copy .env to .env and configure it")
        return
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")
    
    # Import and run main
    try:
        from main import main as bot_main
        import asyncio
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    main()