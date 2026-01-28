import os
import logging
import asyncio
import shutil
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

# ==========================================
# 👇 APNA TOKEN YAHAN DAALO
# ==========================================
TOKEN = "8421035286:AAHwFnb08kgffbTFT3WAV4asG4Zbr2X5meA" 

# ==========================================
# 👇 FLASK WEB SERVER (Render ke liye)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running! (Ye Page Render ko Zinda rakhega)"

def run_flask():
    # Render khud PORT deta hai, agar nahi mila to 8080 use karega
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 👇 BOT LOGIC
# ==========================================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Link bhejo!")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url:
        await update.message.reply_text("❌ Link sahi nahi hai.")
        return

    context.user_data['url'] = url
    keyboard = [
        [InlineKeyboardButton("🎵 MP3 (Audio)", callback_data='type_audio')],
        [InlineKeyboardButton("🎬 Video", callback_data='type_video')]
    ]
    await update.message.reply_text("Format choose karo:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    url = context.user_data.get('url')

    if not url:
        await query.edit_message_text("❌ Link expire ho gaya.")
        return

    if data == 'type_audio':
        keyboard = [[InlineKeyboardButton("Confirm Download", callback_data='aud_best')]]
        await query.edit_message_text("🎵 Audio Download karein?", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'type_video':
        keyboard = [
            [InlineKeyboardButton("360p", callback_data='vid_360'), InlineKeyboardButton("720p", callback_data='vid_720')],
            [InlineKeyboardButton("1080p", callback_data='vid_1080')]
        ]
        await query.edit_message_text("🎬 Quality select karo:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith('aud_') or data.startswith('vid_'):
        await query.edit_message_text("⏳ Download shuru ho raha hai... Wait karo.")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: run_download_task(url, data, update, context))

def run_download_task(url, choice, update, context):
    asyncio.run(execute_download(url, choice, update, context))

async def execute_download(url, choice, update, context):
    chat_id = update.effective_chat.id
    
    if not shutil.which('ffmpeg'):
        await context.bot.send_message(chat_id, "⚠️ Server Error: FFmpeg missing on Server.")
        return

    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['ios']}},
    }

    if 'aud_' in choice:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        })
    elif 'vid_' in choice:
        height = choice.split('_')[1]
        ydl_opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'
        ydl_opts['merge_output_format'] = 'mp4'

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'requested_downloads' in info:
                filename = info['requested_downloads'][0]['filepath']
            else:
                filename = ydl.prepare_filename(info)
                if 'aud_' in choice: filename = filename.rsplit('.', 1)[0] + '.mp3'

        if filename and os.path.exists(filename):
            if os.path.getsize(filename) > 49 * 1024 * 1024:
                await context.bot.send_message(chat_id, "❌ File 50MB se badi hai (Telegram Limit).")
            else:
                await context.bot.send_message(chat_id, "✅ Uploading...")
                with open(filename, 'rb') as f:
                    if 'aud_' in choice:
                        await context.bot.send_audio(chat_id, audio=f, title=info.get('title', 'Audio'))
                    else:
                        await context.bot.send_video(chat_id, video=f, caption=info.get('title', 'Video'))
            os.remove(filename)
        else:
            await context.bot.send_message(chat_id, "❌ File download fail ho gayi.")

    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Error: {str(e)}")
        if filename and os.path.exists(filename): os.remove(filename)

if __name__ == '__main__':
    # --- YAHAN HAI FLASK KA MAGIC ---
    # Threading use karke Flask ko alag chalayenge taaki Bot na ruke
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Bot Start
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    application.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is Live on Render/Pydroid...")
    application.run_polling()
