"""
Authorization management plugin
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import Config

def owner_only(func):
    """Decorator to check owner access"""
    async def wrapper(client: Client, message: Message):
        if message.from_user.id != Config.OWNER_ID:
            await message.reply_text("owner only command")
            return
        return await func(client, message)
    return wrapper

@Client.on_message(filters.command("auth"))
@owner_only
async def auth_command(client: Client, message: Message):
    """Handle authorization management"""
    
    if len(message.command) < 2:
        # Show auth menu
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("add user", callback_data="auth_add_user"),
                InlineKeyboardButton("remove user", callback_data="auth_remove_user")
            ],
            [
                InlineKeyboardButton("add group", callback_data="auth_add_group"),
                InlineKeyboardButton("remove group", callback_data="auth_remove_group")
            ],
            [
                InlineKeyboardButton("list authorized", callback_data="auth_list")
            ]
        ])
        
        await message.reply_text(
            "**authorization management**\n\nselect an option:",
            reply_markup=keyboard
        )
        return
        
    args = message.text.split()
    action = args[1].lower()
    
    if action == "add" and len(args) >= 4:
        entity_type = args[2].lower()  # user or group
        entity_id = int(args[3])
        
        if entity_type == "user":
            client.auth_users.add(entity_id)
            if client.db:
                await client.db.add_auth_user(entity_id)
            await message.reply_text(f"user `{entity_id}` added to authorized users")
            
        elif entity_type == "group":
            client.auth_groups.add(entity_id)
            if client.db:
                await client.db.add_auth_group(entity_id)
            await message.reply_text(f"group `{entity_id}` added to authorized groups")
            
    elif action == "remove" and len(args) >= 4:
        entity_type = args[2].lower()
        entity_id = int(args[3])
        
        if entity_type == "user":
            client.auth_users.discard(entity_id)
            if client.db:
                await client.db.remove_auth_user(entity_id)
            await message.reply_text(f"user `{entity_id}` removed from authorized users")
            
        elif entity_type == "group":
            client.auth_groups.discard(entity_id)
            if client.db:
                await client.db.remove_auth_group(entity_id)
            await message.reply_text(f"group `{entity_id}` removed from authorized groups")
            
    elif action == "list":
        result = "**authorized entities:**\n\n"
        result += f"**owner:** `{Config.OWNER_ID}`\n\n"
        
        if client.auth_users:
            result += "**users:**\n"
            for user_id in client.auth_users:
                result += f"• `{user_id}`\n"
        else:
            result += "**users:** none\n"
            
        result += "\n"
        
        if client.auth_groups:
            result += "**groups:**\n"
            for group_id in client.auth_groups:
                result += f"• `{group_id}`\n"
        else:
            result += "**groups:** none\n"
            
        await message.reply_text(result)
        
    else:
        help_text = """**auth command usage:**

`/auth` - show auth menu
`/auth add user <user_id>` - add authorized user
`/auth add group <group_id>` - add authorized group  
`/auth remove user <user_id>` - remove authorized user
`/auth remove group <group_id>` - remove authorized group
`/auth list` - list all authorized entities

**examples:**
`/auth add user 123456789`
`/auth add group -100123456789`
`/auth remove user 123456789`"""

        await message.reply_text(help_text)