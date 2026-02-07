import os
import asyncio
import time
import threading
import requests
import yt_dlp
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- ⚙️ CONFIGURATION (Render Environment Variables) ---
API_ID = int(os.environ.get("API_ID", "37314366"))
API_HASH = os.environ.get("API_HASH", "bd4c934697e7e91942ac911a5a287b46")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8421035286:AAHNFAIgzmBESZTkk7ErPz1-DH2FkWRUSWs")

# --- 🌐 FLASK SERVER (Render ko zinda rakhne ke liye) ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "✅ Bot is Online and Running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

# --- 🤖 BOT CLIENT ---
app = Client("RenderApiBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 🔗 STRICT API LIST ---
MP3_API = "https://ytmp3.alphaapi.workers.dev/?url={}"
MP4_API = "https://ytmp4hd1080p.anshapi.workers.dev/down?url={}&format=1&quality=1080"

# --- 🛠️ IMPORTANT: Browser Headers (Playback Fix) ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# --- 🔍 HELPER ---
def get_yt_link(query):
    if "youtube.com" in query or "youtu.be" in query: return query
    ydl_opts = {'format': 'best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch1'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            return info['entries'][0]['webpage_url'] if 'entries' in info else None
        except: return None

# --- 📥 API DOWNLOADER ---
def download_from_api(url, mode):
    filename = f"song_{int(time.time())}"
    final_path = f"{filename}.{'mp3' if mode == 'mp3' else 'mp4'}"
    
    target_api = MP3_API if mode == 'mp3' else MP4_API
    formatted_url = target_api.format(url)
    
    print(f"🔄 Connecting to API for {mode}...")
    
    try:
        # 1. API Response
        resp = requests.get(formatted_url, headers=HEADERS, timeout=15).json()
        
        # 2. Link Extraction Logic
        dl_link = None
        def extract(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, str) and v.startswith("http"): return v
                    if isinstance(v, (dict, list)): 
                        res = extract(v)
                        if res: return res
            elif isinstance(d, list):
                for i in d:
                    res = extract(i)
                    if res: return res
            return None

        if 'url' in resp: dl_link = resp['url']
        elif 'download' in resp: dl_link = resp['download']
        elif 'link' in resp: dl_link = resp['link']
        
        if not dl_link: dl_link = extract(resp)
        
        if dl_link:
            print(f"✅ Link Found: {dl_link}")
            
            # 3. Download Content (With Headers to fix Playback)
            with requests.get(dl_link, headers=HEADERS, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(final_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            # 4. Size Validation
            if os.path.getsize(final_path) > 50000: # 50KB check
                return final_path
            else:
                os.remove(final_path)
                return None
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# --- 💬 START ---
@app.on_message(filters.command("start"))
async def start(client, message):
    txt = (
        f"👋 **Hello {message.from_user.first_name}!**\n\n"
        "🎶 **Music & Video Downloader Bot**\n"
        "ℹ️ **Render Support:** Yes (24/7)\n"
        "🚀 **Speed:** High Speed API\n\n"
        "👇 **Song ka naam ya Link bhejo:**"
    )
    # Mast Photo (Badal sakte ho)
    IMG = "https://graph.org/file/460960527351658428178.jpg"
    
    await message.reply_photo(IMG, caption=txt)

# --- 🔎 PROCESS ---
@app.on_message(filters.text)
async def handle_msg(client, message):
    if message.text.startswith("/"): return
    
    msg = await message.reply_text("🔎 **Searching...**")
    url = await asyncio.get_event_loop().run_in_executor(None, get_yt_link, message.text)
    
    if not url:
        await msg.edit("❌ Song nahi mila.")
        return

    # Metadata Fetch (Sirf Display ke liye)
    title = "Unknown"
    thumb = None
    try:
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            thumb = info.get('thumbnail')
            duration = info.get('duration_string')
    except: pass

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 MP3 Song", callback_data=f"mp3|{url}")],
        [InlineKeyboardButton("🎥 HD Video", callback_data=f"mp4|{url}")]
    ])
    
    caption = f"💿 **{title}**\n⏱ **Duration:** {duration}\n\n👇 Format Select Karo:"
    
    if thumb: await message.reply_photo(thumb, caption=caption, reply_markup=btn)
    else: await message.reply_text(caption, reply_markup=btn)
    await msg.delete()

@app.on_callback_query()
async def cb(client, query):
    mode, url = query.data.split("|")
    status = await query.message.reply_text("⚡ **Connecting to Server...**")
    
    try:
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_from_api, url, mode)
        
        if file_path:
            await status.edit("🚀 **Uploading...**")
            
            # Metadata for Player
            title = "Music"
            performer = "Render Bot"
            duration = 0
            try:
                with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', title)
                    performer = info.get('uploader', performer)
                    duration = info.get('duration', 0)
            except: pass

            if mode == 'mp3':
                await client.send_audio(
                    chat_id=query.message.chat.id,
                    audio=file_path,
                    title=title,
                    performer=performer,
                    duration=duration,
                    caption=f"🎧 **{title}**\n✨ High Quality MP3"
                )
            else:
                await client.send_video(
                    chat_id=query.message.chat.id,
                    video=file_path,
                    duration=duration,
                    caption=f"🎬 **{title}**\n✨ HD Video"
                )
            
            os.remove(file_path)
            await status.delete()
        else:
            await status.edit("❌ **Error:** API se file load nahi ho payi.")
            
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

if __name__ == "__main__":
    # Flask Thread Start
    threading.Thread(target=run_flask).start()
    print("✅ Bot + Flask Started!")
    app.run()
