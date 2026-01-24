import os, yt_dlp, asyncio, uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# --- CONFIGURATION ---
# Render ke Environment Variables mein BOT_TOKEN set karein
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8421035286:AAHAXb-OI-kqiQnM7UL42o1JervTtQFT9fg"
OWNER_TAG = "👑 Owner: Naeem (F4X Empire)"

def get_video_info(url):
    ydl_opts = {
        'quiet': True, 'no_warnings': True,
        # Anti-Block: Spoofing as Android to avoid being caught as a bot
        'extractor_args': {'youtube': {'player_client': ['android', 'web_embedded']}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def download_engine(url, mode, f_id=None):
    uid = str(uuid.uuid4())[:8]
    file_template = f"f4x_{uid}.%(ext)s"
    opts = {
        'outtmpl': file_template, 'noplaylist': True, 'quiet': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Android 14; Mobile; rv:128.0)'},
    }
    if mode == 'mp3':
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'm4a'}]
    else:
        # Docker/FFmpeg high quality merging handle karega
        opts['format'] = f"{f_id}+bestaudio/best" if f_id else 'bestvideo+bestaudio/best'
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def start(u, c): 
    await u.message.reply_text(f"🚀 **F4X Ultra Downloader Ready!**\n\nNaeem bhai, link bhejien. 4K tak support hai!\n\n{OWNER_TAG}")

async def handle_msg(u, c):
    q = u.message.text
    if "playlist" in q: return await u.message.reply_text("❌ Playlist not supported. Single video link bhejien.")
    
    st = await u.message.reply_text("🛰️ F4X Engine Analyzing Quality...")
    try:
        info = await asyncio.get_event_loop().run_in_executor(None, get_video_info, q)
        v_url = info['webpage_url']
        btns = [[InlineKeyboardButton("🎵 Audio (Ultra High)", callback_data=f"mp3|audio|{v_url}")]]
        
        # Adding High Quality Options
        qualities = [(720, "22", "HD"), (1080, "137", "Full HD"), (1440, "308", "2K"), (2160, "401", "4K Ultra")]
        for res, f_id, label in qualities:
            btns.append([InlineKeyboardButton(f"🎥 {label} ({res}p)", callback_data=f"mp4|{f_id}|{v_url}|{res}")])
            
        await st.edit_text(f"🎬 **Title**: {info['title'][:50]}...\n\nSahi quality select karein:", reply_markup=InlineKeyboardMarkup(btns))
    except: await st.edit_text("❌ Video detail nahi mili. Sahi link bhejien.")

async def button_handler(u, c):
    query = u.callback_query; await query.answer()
    data = query.data.split("|")
    mode, f_id, url = data[0], data[1], data[2]
    res_val = int(data[3]) if len(data) > 3 else 0

    if res_val >= 1440:
        await query.message.reply_text(f"⚠️ **Note**: {res_val}p ke liye heavy file hogi. Agar phone support na kare toh 1080p try karein.")

    st = await query.message.reply_text("⏳ F4X Cloud Downloading (Heavy Process)...")
    try:
        path = await asyncio.get_event_loop().run_in_executor(None, download_engine, url, mode, f_id if f_id != 'audio' else None)
        await st.edit_text("📤 Uploading to Telegram...")
        with open(path, 'rb') as f:
            if mode == 'mp3': await query.message.reply_audio(audio=f, caption=OWNER_TAG)
            else: await query.message.reply_video(video=f, caption=OWNER_TAG, supports_streaming=True)
        if os.path.exists(path): os.remove(path)
        await st.delete()
    except Exception as e: await st.edit_text(f"⚠️ Error: Download fail ho gaya.")

if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(button_handler)); app.run_polling()
    
