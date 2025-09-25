"""
Plugin loader for MuxBot
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_plugins():
    """Load all plugins"""
    plugins_dir = Path(__file__).parent
    plugin_files = plugins_dir.glob("*.py")
    
    loaded = 0
    for plugin_file in plugin_files:
        if plugin_file.name.startswith("_"):
            continue
            
        try:
            plugin_name = plugin_file.stem
            __import__(f"bot.plugins.{plugin_name}")
            loaded += 1
            logger.info(f"loaded plugin: {plugin_name}")
        except Exception as e:
            logger.error(f"failed to load plugin {plugin_file.name}: {e}")
            
    logger.info(f"loaded {loaded} plugins")