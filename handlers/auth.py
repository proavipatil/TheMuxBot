"""Authorization handlers"""

from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config, OWNER_ID, AUTHORIZED_USERS, AUTHORIZED_GROUPS
from database import db

@Client.on_message(filters.command("auth"))
async def auth_handler(client: Client, message: Message):
    """Handle /auth command"""
    user_id = message.from_user.id
    
    # Only owner can authorize users
    if user_id != OWNER_ID:
        await message.reply_text("⚠️ **owner access required**", quote=True)
        return
    
    if len(message.command) < 2:
        await message.reply_text(
            "**usage:** `/auth <user_id>` or `/auth <group_id>`\n\n"
            "**examples:**\n"
            "• `/auth 123456789` - authorize user\n"
            "• `/auth -100123456789` - authorize group",
            quote=True
        )
        return
    
    try:
        target_id = int(message.command[1])
        
        if target_id < 0:  # Group ID
            if target_id not in AUTHORIZED_GROUPS:
                AUTHORIZED_GROUPS.append(target_id)
                await db.add_auth_group(target_id)
                await message.reply_text(
                    f"✅ **group authorized**\n\n**group id:** `{target_id}`",
                    quote=True
                )
            else:
                await message.reply_text(
                    f"ℹ️ **group already authorized**\n\n**group id:** `{target_id}`",
                    quote=True
                )
        else:  # User ID
            if target_id not in AUTHORIZED_USERS:
                AUTHORIZED_USERS.append(target_id)
                await db.add_auth_user(target_id)
                await message.reply_text(
                    f"✅ **user authorized**\n\n**user id:** `{target_id}`",
                    quote=True
                )
            else:
                await message.reply_text(
                    f"ℹ️ **user already authorized**\n\n**user id:** `{target_id}`",
                    quote=True
                )
                
    except ValueError:
        await message.reply_text("❌ **invalid id format**", quote=True)
    except Exception as e:
        await message.reply_text(f"❌ **error:** `{str(e)}`", quote=True)

@Client.on_message(filters.command("unauth"))
async def unauth_handler(client: Client, message: Message):
    """Handle /unauth command"""
    user_id = message.from_user.id
    
    # Only owner can unauthorize users
    if user_id != OWNER_ID:
        await message.reply_text("⚠️ **owner access required**", quote=True)
        return
    
    if len(message.command) < 2:
        await message.reply_text(
            "**usage:** `/unauth <user_id>` or `/unauth <group_id>`",
            quote=True
        )
        return
    
    try:
        target_id = int(message.command[1])
        
        if target_id < 0:  # Group ID
            if target_id in AUTHORIZED_GROUPS:
                AUTHORIZED_GROUPS.remove(target_id)
                await db.remove_auth_group(target_id)
                await message.reply_text(
                    f"✅ **group unauthorized**\n\n**group id:** `{target_id}`",
                    quote=True
                )
            else:
                await message.reply_text(
                    f"ℹ️ **group not in authorized list**\n\n**group id:** `{target_id}`",
                    quote=True
                )
        else:  # User ID
            if target_id in AUTHORIZED_USERS:
                AUTHORIZED_USERS.remove(target_id)
                await db.remove_auth_user(target_id)
                await message.reply_text(
                    f"✅ **user unauthorized**\n\n**user id:** `{target_id}`",
                    quote=True
                )
            else:
                await message.reply_text(
                    f"ℹ️ **user not in authorized list**\n\n**user id:** `{target_id}`",
                    quote=True
                )
                
    except ValueError:
        await message.reply_text("❌ **invalid id format**", quote=True)
    except Exception as e:
        await message.reply_text(f"❌ **error:** `{str(e)}`", quote=True)

@Client.on_message(filters.command("authlist"))
async def authlist_handler(client: Client, message: Message):
    """Handle /authlist command"""
    user_id = message.from_user.id
    
    # Only owner can view auth list
    if user_id != OWNER_ID:
        await message.reply_text("⚠️ **owner access required**", quote=True)
        return
    
    try:
        auth_users = await db.get_auth_users()
        auth_groups = await db.get_auth_groups()
        
        text = "👥 **authorization list**\n\n"
        
        text += f"**owner:** `{OWNER_ID}`\n\n"
        
        if auth_users:
            text += "**authorized users:**\n"
            for user in auth_users:
                text += f"• `{user}`\n"
            text += "\n"
        else:
            text += "**authorized users:** none\n\n"
        
        if auth_groups:
            text += "**authorized groups:**\n"
            for group in auth_groups:
                text += f"• `{group}`\n"
        else:
            text += "**authorized groups:** none"
        
        await message.reply_text(text, quote=True)
        
    except Exception as e:
        await message.reply_text(f"❌ **error:** `{str(e)}`", quote=True)