import os, yt_dlp, asyncio, uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8421035286:AAHAXb-OI-kqiQnM7UL42o1JervTtQFT9fg"
OWNER_TAG = "👑 Owner: Naeem (F4X Empire)"

def download_engine(url, mode, f_id=None):
    uid = str(uuid.uuid4())[:8]
    tmpl = f"f4x_{uid}.%(ext)s"
    opts = {
        'outtmpl': tmpl, 'noplaylist': True, 'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web_embedded']}},
    }
    if mode == 'mp3':
        opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'm4a'}]})
    else:
        opts['format'] = f"{f_id}+bestaudio/best" if f_id else 'bestvideo+bestaudio/best'
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def start(u, c):
    await u.message.reply_text(f"🚀 **F4X 4K Ultra System Ready!**\nNaeem bhai, link bhejien.\n\n{OWNER_TAG}")

async def handle_msg(u, c):
    q = u.message.text
    if "playlist" in q: return await u.message.reply_text("❌ Single video link bhejien.")
    st = await u.message.reply_text("🛰️ Analyzing Quality Options...")
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(q if q.startswith("http") else f"ytsearch1:{q}", download=False)
            if 'entries' in info: info = info['entries'][0]
        v_url = info['webpage_url']
        btns = [[InlineKeyboardButton("🎵 Audio", callback_data=f"mp3|audio|{v_url}")],
                [InlineKeyboardButton("🎥 1080p", callback_data=f"mp4|137|{v_url}"),
                 InlineKeyboardButton("🎥 4K Ultra", callback_data=f"mp4|401|{v_url}")]]
        await st.edit_text(f"🎬 {info['title'][:40]}\nQuality select karein:", reply_markup=InlineKeyboardMarkup(btns))
    except: await st.edit_text("❌ Error: Detail nahi mili.")

async def btn_click(u, c):
    query = u.callback_query; await query.answer()
    m, f_id, url = query.data.split("|")
    st = await query.message.reply_text("⏳ Processing (High Quality Merge)...")
    try:
        path = await asyncio.get_event_loop().run_in_executor(None, download_engine, url, m, f_id)
        await st.edit_text("📤 Uploading...")
        with open(path, 'rb') as f:
            if m == 'mp3': await query.message.reply_audio(audio=f, caption=OWNER_TAG)
            else: await query.message.reply_video(video=f, caption=OWNER_TAG, supports_streaming=True)
        os.remove(path); await st.delete()
    except Exception as e: await st.edit_text(f"⚠️ Error: {str(e)[:50]}")

if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(btn_click)); app.run_polling()
