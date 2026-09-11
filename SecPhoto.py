# SecPhoto - Pyrogram Version for Google Colab
# github.com/YOUR_USERNAME/SecPhoto

from pyrogram import Client, filters
from pyrogram.types import Message
import os
import shutil
from datetime import datetime
import asyncio

# ============================================
# CONFIGURATION - CHANGE THESE
# ============================================

# Your Telegram API credentials from my.telegram.org
API_ID = 1234567  # Replace with your api_id
API_HASH = "your_api_hash_here"  # Replace with your api_hash

# Session string (get this from your existing Pyrogram session)
# OR leave empty to use session file
SESSION_STRING = ""

# Google Drive path for session backup
DRIVE_PATH = "/content/drive/MyDrive/SecPhoto"

# ============================================
# SESSION SETUP
# ============================================

def setup_session():
    """Setup session from Drive or create new"""
    os.makedirs(DRIVE_PATH, exist_ok=True)

    local_session = "/content/SecPhoto/secret.session"
    drive_session = f"{DRIVE_PATH}/secret.session"

    # Copy from Drive if exists
    if os.path.exists(drive_session):
        shutil.copy(drive_session, local_session)
        print("✓ Session loaded from Google Drive")
        return True
    else:
        print("✗ No session found - will create new one")
        return False

def save_session():
    """Save session to Drive"""
    local_session = "/content/SecPhoto/secret.session"
    drive_session = f"{DRIVE_PATH}/secret.session"

    if os.path.exists(local_session):
        shutil.copy(local_session, drive_session)
        print("✓ Session saved to Google Drive")

# ============================================
# BOT SETUP
# ============================================

# Initialize client
if SESSION_STRING:
    app = Client(
        "secret",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )
else:
    app = Client(
        "secret",
        api_id=API_ID,
        api_hash=API_HASH
    )

# ============================================
# HELPER FUNCTIONS
# ============================================

def is_self_destructive(message: Message) -> bool:
    """Check if message has self-destructing media"""
    if not message.media:
        return False

    # Check for TTL (time to live) attribute
    if hasattr(message, 'ttl_seconds') and message.ttl_seconds:
        return True

    # Check media attributes
    if message.photo and hasattr(message.photo, 'ttl_seconds') and message.photo.ttl_seconds:
        return True

    if message.video and hasattr(message.video, 'ttl_seconds') and message.video.ttl_seconds:
        return True

    return False

def build_caption(message: Message, chat_title: str, is_reply: bool = False) -> str:
    """Build caption for saved media"""
    chat_id = message.chat.id
    username = message.chat.username if message.chat.username else "✗"
    msg_id = message.id
    date_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    prefix = "┏" if not is_reply else "┣"
    reply_text = "┏ᖇᗴᑭᒪIᗴᗴᗪ TO ᗰᗴՏՏᗩᘜᗴ\n" if is_reply else ""

    caption = (
        f"{reply_text}"
        f"{prefix}ᑕᕼᗩT Iᗪ ⤳ {chat_id}\n"
        f"┣ᑌՏᗴᖇᑎᗩᗰᗴ ⤳ @{username}\n"
        f"┣ᗰᗴՏՏᗩᘜᗴ Iᗪ ⤳ {msg_id}\n"
        f"┣ᗪᗩTᗴ TIᗰᗴ ⤳ {date_time}\n"
        f"┗ SecPhoto"
    )
    return caption

async def save_media(client: Client, message: Message, is_reply: bool = False):
    """Download and save self-destructing media"""
    try:
        chat_title = message.chat.title or message.chat.first_name or "Unknown"

        # Build filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        username = message.chat.username or str(message.chat.id)

        # Sanitize filename
        for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            username = username.replace(char, '_')

        # Determine file type
        if message.photo:
            ext = "jpg"
            media_type = "photo"
        elif message.video:
            ext = "mp4"
            media_type = "video"
        else:
            ext = "media"
            media_type = "media"

        filename = f"{username}_{timestamp}.{ext}"

        print(f"↓ Downloading {media_type} from {chat_title}...")

        # Download media
        path = await message.download(file_name=filename)

        if path and os.path.exists(path):
            # Build caption
            caption = build_caption(message, chat_title, is_reply)

            # Send to Saved Messages
            if media_type == "photo":
                await client.send_photo("me", path, caption=caption)
            elif media_type == "video":
                await client.send_video("me", path, caption=caption)
            else:
                await client.send_document("me", path, caption=caption)

            print(f"✓ Saved {media_type} from {chat_title}")

            # Delete temp file
            os.remove(path)
        else:
            print(f"✗ Failed to download from {chat_title}")

    except Exception as e:
        print(f"✗ Error: {str(e)}")

# ============================================
# HANDLERS
# ============================================

@app.on_message(filters.incoming & filters.media)
async def handle_new_media(client: Client, message: Message):
    """Handle new self-destructing media"""
    if is_self_destructive(message):
        await save_media(client, message, is_reply=False)

@app.on_message(filters.incoming & filters.reply & filters.media)
async def handle_reply_media(client: Client, message: Message):
    """Handle replied-to self-destructing media"""
    try:
        replied = await message.get_reply_message()
        if replied and is_self_destructive(replied):
            await save_media(client, replied, is_reply=True)
    except Exception as e:
        print(f"✗ Reply error: {str(e)}")

# ============================================
# MAIN
# ============================================

async def main():
    print("=" * 50)
    print("SecPhoto - Pyrogram Version")
    print("=" * 50)
    print()

    # Setup session
    has_session = setup_session()

    # Start client
    await app.start()

    me = await app.get_me()
    print(f"✓ Logged in as: {me.first_name} (@{me.username})")
    print()
    print("Monitoring all chats for self-destructing media...")
    print("Reply to any message to save its media")
    print("Press Ctrl+C to stop")
    print()

    # Save session to Drive
    save_session()

    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")
    except Exception as e:
        print(f"Error: {str(e)}")
        
