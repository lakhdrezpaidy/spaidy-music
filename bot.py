import web
import asyncio
import os
import re
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
import yt_dlp

API_ID = 25463867
API_HASH = "f8616f4968fb92904faa7c4790e2eb27"
BOT_TOKEN = "8570956126:AAGUlv2j16rHf4Drz0NfN1SCoKpBx5Yeoy4"
BOT_USERNAME = "Spaidyx8_u_bot"

bot = Client("SpaidyAudioBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

disabled_chats = set()

FAST_DOWNLOAD_OPTS = {
    'format': 'bestaudio[ext=m4a]/ba[filesize<30M]/ba/b',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch1:',
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'noplaylist': True,
        'cookiefile': 'cookies.txt',
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
    'socket_timeout': 15,
}

def download_audio_safe(query: str):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    with yt_dlp.YoutubeDL(FAST_DOWNLOAD_OPTS) as ydl:
        res = ydl.extract_info(query, download=True)
        if 'entries' in res and res['entries']:
            res = res['entries'][0]

        video_id = res['id']
        title = res.get('title', 'صوت غير معروف')
        duration = res.get('duration', 0)
        thumb_url = res.get('thumbnail')

        audio_file = None
        for f in os.listdir("downloads"):
            if f.startswith(video_id) and not f.endswith('.part'):
                full_path = os.path.join("downloads", f)
                if os.path.getsize(full_path) > 1024:
                    audio_file = full_path
                    break

        return audio_file, thumb_url, title, duration, video_id

async def download_thumb(url: str, path: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    with open(path, 'wb') as f:
                        f.write(await resp.read())
                    return True
    except Exception:
        pass
    return False

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(_, message: Message):
    welcome_text = (
        f"👋 مرحباً بك {message.from_user.mention}!\n\n"
        "🎶 أنا بوت **سبايدي ميوزك** السحابي فائق السرعة.\n\n"
        "⚡ للتشغيل داخل القروبات:\n"
        "`يوت + اسم المقطع`\n\n"
        "🛠 التحكم (للمشرفين):\n"
        "• `تعطيل اليوتيوب`\n"
        "• `تفعيل اليوتيوب`\n\n"
        "👇 اضغط أدناه لإضافتي لمجموعتك:"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ أضفني إلى مجموعتك",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
            )
        ]
    ])
    await message.reply_text(welcome_text, reply_markup=keyboard)

@bot.on_message(filters.text & filters.group)
async def handle_group_msg(_, message: Message):
    text = message.text.strip()
    chat_id = message.chat.id

    if text in ["تعطيل اليوتيوب", "قفل اليوتيوب"]:
        member = await message.chat.get_member(message.from_user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            disabled_chats.add(chat_id)
            await message.reply_text("🚫 **تم تعطيل اليوتيوب في هذه المجموعة.**")
        else:
            await message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
        return

    elif text in ["تفعيل اليوتيوب", "فتح اليوتيوب"]:
        member = await message.chat.get_member(message.from_user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            disabled_chats.discard(chat_id)
            await message.reply_text("✅ **تم تفعيل اليوتيوب في المجموعة بنجاح!**")
        else:
            await message.reply_text("⚠️ هذا الأمر للمشرفين فقط!")
        return

    if text.startswith("يوت"):
        if chat_id in disabled_chats:
            return

        query = re.sub(r"^يوت\s*", "", text).strip()
        if not query:
            return await message.reply_text("يرجى كتابة اسم المقطع، مثال:\n`يوت faded`")

        status_msg = await message.reply_text("سبايدي يبحث ....")

        try:
            loop = asyncio.get_running_loop()
            audio_file, thumb_url, title, duration, video_id = await loop.run_in_executor(None, download_audio_safe, query)

            if not audio_file:
                return await status_msg.edit_text("تعذر تحميل المقطع الصوتي، جرب اسماً آخر.")

            thumb_file = f"downloads/{video_id}.jpg"
            has_thumb = False
            if thumb_url:
                has_thumb = await download_thumb(thumb_url, thumb_file)

            await message.reply_audio(
                audio=audio_file,
                thumb=thumb_file if has_thumb and os.path.exists(thumb_file) else None,
                title=title,
                performer="Spaidy Music",
                duration=duration,
                caption=f"🎵 **{title}**\n\n👤 طلب بواسطة: {message.from_user.mention}"
            )

            await status_msg.delete()

            if os.path.exists(audio_file):
                os.remove(audio_file)
            if has_thumb and os.path.exists(thumb_file):
                os.remove(thumb_file)

        except Exception as e:
            await status_msg.edit_text(f"خطأ أثناء التحميل: `{e}`")

print("البوت السحابي جاهز للعمل...")
bot.run()
