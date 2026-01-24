import os, yt_dlp, asyncio, uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# --- APNA TOKEN YAHAN DAALO ---
BOT_TOKEN = "8421035286:AAHAXb-OI-kqiQnM7UL42o1JervTtQFT9fg"
OWNER_TAG = "👑 Owner: Naeem (F4X Empire)"

# --- DOWNLOAD ENGINE (NO-BLOCK SETTINGS) ---
def download_engine(url, mode, quality=None):
    unique_id = str(uuid.uuid4())[:8]
    file_tmpl = f"f4x_{unique_id}.%(ext)s"
    
    # Quality Logic
    if mode == 'mp3':
        f_str = 'bestaudio/best'
    else:
        # Render par 4K/1080p ke liye strict rule
        if quality == "best":
            f_str = 'bestvideo+bestaudio/best'
        else:
            f_str = f'bestvideo[height<={quality}]+bestaudio/best[ext=mp4]/best'

    # --- YE HAI ANTI-BLOCK SETTING ---
    ydl_opts = {
        'outtmpl': file_tmpl,
        'format': f_str,
        'noplaylist': True,
        'merge_output_format': 'mp4', # Video+Audio jodega
        'quiet': True,
        'geo_bypass': True,
        # YouTube ko ullu banane ke liye Android Client bano
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs', 'js'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def start(u, c):
    await u.message.reply_text(f"🔥 **F4X Ultra Downloader Active!**\nLink bhejo aur quality choose karo.\n\n{OWNER_TAG}")

async def handle_msg(u, c):
    url = u.message.text
    if "youtu" in url:
        btns = [
            [InlineKeyboardButton("🎥 Select Quality", callback_data=f"qual|{url}")],
            [InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"mp3|{url}")]
        ]
        await u.message.reply_text("Format select karein:", reply_markup=InlineKeyboardMarkup(btns))
    else:
        await u.message.reply_text("❌ Ye YouTube link nahi hai.")

async def btn_click(u, c):
    query = u.callback_query; await query.answer()
    data = query.data.split("|")
    task = data[0]
    url = data[1]

    if task == "qual":
        q_btns = [
            [InlineKeyboardButton("360p (Low)", callback_data=f"360|{url}"), InlineKeyboardButton("720p (HD)", callback_data=f"720|{url}")],
            [InlineKeyboardButton("1080p (Full HD)", callback_data=f"1080|{url}"), InlineKeyboardButton("4K (Ultra)", callback_data=f"2160|{url}")],
        ]
        await query.message.edit_text("Video Quality Select Karein:", reply_markup=InlineKeyboardMarkup(q_btns))
        return

    st = await query.message.reply_text(f"⏳ **Downloading {task}...**\nBadi video mein time lag sakta hai.")
    try:
        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(None, download_engine, url, 'mp4' if task != 'mp3' else 'mp3', task)
        
        file_size = os.path.getsize(path) / (1024 * 1024) # MB mein size
        
        if file_size > 49:
            await st.edit_text(f"⚠️ **File Badi Hai ({int(file_size)}MB)**\nTelegram Bot limit 50MB hai. Main upload nahi kar sakta.")
            os.remove(path)
        else:
            await st.edit_text("📤 **Uploading to Telegram...**")
            with open(path, 'rb') as f:
                if task == 'mp3': await query.message.reply_audio(audio=f, caption=OWNER_TAG)
                else: await query.message.reply_video(video=f, caption=OWNER_TAG, supports_streaming=True)
            if os.path.exists(path): os.remove(path)
            await st.delete()

    except Exception as e:
        await st.edit_text(f"❌ Error: {str(e)}\n(Shayad video private hai ya server block hua hai)")

if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(btn_click))
    print("✅ F4X Bot Ready on Render!")
    app.run_polling()
