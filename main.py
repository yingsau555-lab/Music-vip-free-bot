import os
import json
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
import yt_dlp

# ==================== CONFIGURATION ====================
API_ID = 32858139
API_HASH = "37873e2c933428875670b413e1"
BOT_TOKEN = "8275882833:AAEsizmVfflM-fqbZWDXeatgaXNWRCInomU"
ADMIN_ID = 5159757736

PAYMENT_INFO = """
 **VIP ဝယ်ယူရန် ငွေပေးချေမှု အချက်အလက်များ** 

 **KPay:** Hpare Ying Sau
 **ဖုန်းနံပါတ်:** `09424305728`

 **Wave Pay:** Eaindra Aung
 **ဖုန်းနံပါတ်:** `09792020879`

 **VIP ဈေးနှုန်းများ:**
 1 လ - 3,000 MMK
 3 လ - 8,000 MMK
 တစ်သက်တာ (Lifetime) - 20,000 MMK

 *ငွေလွှဲပြီးပါက ငွေလွှဲစလစ် (Screenshot) ကို ဤ Bot ထဲသို့ တိုက်ရိုက် ပို့ပေးပါ!*
"""

# ==================== SIMPLE DATABASE ====================
DB_FILE = "users_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"vips": {}, "daily_limits": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

def is_vip(user_id):
    user_str = str(user_id)
    if user_id == ADMIN_ID:
        return True
    if user_str in db["vips"]:
        exp = datetime.strptime(db["vips"][user_str], "%Y-%m-%d %H:%M:%S")
        if exp > datetime.now():
            return True
        else:
            del db["vips"][user_str]
            save_db(db)
    return False

def check_daily_limit(user_id):
    if is_vip(user_id):
        return True
    user_str = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user_str not in db["daily_limits"]:
        db["daily_limits"][user_str] = {"date": today, "count": 0}
    
    user_data = db["daily_limits"][user_str]
    if user_data["date"] != today:
        user_data["date"] = today
        user_data["count"] = 0
        
    if user_data["count"] < 3: # FREE Limit = 3 Songs/day
        user_data["count"] += 1
        save_db(db)
        return True
    return False

# ==================== PYROGRAM & PYTGCALLS SETUP ====================
app = Client("music_vip_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

def get_audio_url(query: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            return info['entries'][0]['url'], info['entries'][0]['title']
        return info['url'], info['title']

# ==================== COMMAND HANDLERS ====================

@app.on_message(filters.command("start"))
async def start_cmd(_, message: Message):
    status = " VIP Member" if is_vip(message.from_user.id) else " Free Member (3 Songs/Day)"
    msg = (
        f" **MUSIC VIP PREMIUM BOT သို့ ကြိုဆိုပါတယ်!**\n\n"
        f" **သင့် အဆင့်:** {status}\n\n"
        f" **Command များ:**\n"
        f" `/play <သီချင်းအမည်>` - Group Voice Chat ထဲ သီချင်းဖွင့်ရန်\n"
        f" `/song <သီချင်းအမည်>` - MP3 ဖိုင် တိုက်ရိုက် ဒေါင်းလုဒ်ဆွဲရန်\n"
        f" `/vip` - VIP ဝယ်ယူရန် အချက်အလက်များ ကြည့်ရန်\n"
        f" `/myplan` - သင့် VIP သက်တမ်း စစ်ဆေးရန်\n"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(" VIP ဝယ်ယူရန်", callback_data="buy_vip")],
        [InlineKeyboardButton(" Support / Admin", url="https://t.me/telegram")]
    ])
    await message.reply_text(msg, reply_markup=buttons)

@app.on_message(filters.command("vip"))
async def vip_info(_, message: Message):
    await message.reply_text(PAYMENT_INFO)

@app.on_message(filters.callbackquery)
async def callback_handler(_, query: CallbackQuery):
    if query.data == "buy_vip":
        await query.message.edit_text(PAYMENT_INFO)

@app.on_message(filters.command("myplan"))
async def myplan_cmd(_, message: Message):
    user_str = str(message.from_user.id)
    if is_vip(message.from_user.id):
        exp = db["vips"].get(user_str, "Lifetime/Admin")
        await message.reply_text(f" **VIP Active!**\n သက်တမ်းကုန်ဆုံးမည့်ရက်: `{exp}`")
    else:
        await message.reply_text(" သင့်အကောင့်သည် Free Plan ဖြစ်ပါသည် (တစ်နေ့ ၃ ပုဒ် ရရှိပါမည်)။\nVIP သို့ Upgrade ပြုလုပ်ရန် `/vip` ကို နှိပ်ပါ။")

# ==================== MUSIC PLAY & DOWNLOAD ====================

@app.on_message(filters.command("play") & filters.group)
async def play_cmd(_, message: Message):
    user_id = message.from_user.id
    if not check_daily_limit(user_id):
        await message.reply_text(" **Daily Limit ပြည့်သွားပါပြီ!**\nယနေ့အတွက် Free 3 ပုဒ် ပြည့်သွားပါပြီ။ Unlimited သုံးနိုင်ရန် VIP ဝယ်ယူပါ။ (`/vip`)")
        return

    if len(message.command) < 2:
        await message.reply_text(" ကျေးဇူးပြု၍ သီချင်းအမည် ထည့်ပါ။ ဥပမာ - `/play Faded`")
        return

    query = " ".join(message.command[1:])
    status = await message.reply_text(" **သီချင်း ရှာဖွေနေပါသည်...**")

    try:
        stream_url, title = get_audio_url(query)
        await call_py.join_group_call(
            message.chat.id,
            AudioPiped(stream_url)
        )
        vip_tag = " VIP High Quality" if is_vip(user_id) else " Free Quality"
        await status.edit_text(f" **ယခုဖွင့်နေသည့် သီချင်း:** {title}\n **Audio Mode:** {vip_tag}")
    except Exception as e:
        await status.edit_text(f" အမှားတစ်ခု ရှိနေပါသည်: {e}\n(Group Voice Chat စတင်ထားခြင်း ရှိမရှိ စစ်ဆေးပါ)")

# Screenshot (ငွေလွှဲစလစ်) မိမိထံသို့ Auto-Forward ပို့ပေးခြင်း
@app.on_message(filters.photo & filters.private)
async def screenshot_handler(_, message: Message):
    caption = (
        f" **ငွေလွှဲစလစ် အသစ်ရောက်ရှိလာပါသည်။**\n\n"
        f" **User:** {message.from_user.mention}\n"
        f" **User ID:** `{message.from_user.id}`\n\n"
        f" **VIP ပေးရန် Command:**\n"
        f"`/addvip {message.from_user.id} 30` (30 ရက်အတွက်)"
    )
    await message.forward(ADMIN_ID)
    await app.send_message(ADMIN_ID, caption)
    await message.reply_text(" ငွေလွှဲစလစ်အား Admin ထံ ပေးပို့လိုက်ပါပြီ။ စစ်ဆေးပြီးပါက VIP စနစ် အလိုအလျောက် ပွင့်သွားပါမည်။")

# ==================== ADMIN CONTROLS ====================

@app.on_message(filters.command("addvip") & filters.user(ADMIN_ID))
async def add_vip_cmd(_, message: Message):
    try:
        args = message.command
        target_id = args[1]
        days = int(args[2])
        
        exp_date = datetime.now() + timedelta(days=days)
        db["vips"][str(target_id)] = exp_date.strftime("%Y-%m-%d %H:%M:%S")
        save_db(db)
        
        await message.reply_text(f" User `{target_id}` အား VIP သက်တမ်း {days} ရက် ပေးလိုက်ပါပြီ။")
        await app.send_message(int(target_id), f" **ဂုဏ်ယူပါတယ်! သင့်ထံသို့ VIP သက်တမ်း {days} ရက် ထည့်သွင်းပေးလိုက်ပါပြီ။**\nယခုမှစ၍ Unlimited သီချင်းများ သုံးနိုင်ပါပြီ။")
    except Exception as e:
        await message.reply_text(f" Syntax: `/addvip <user_id> <days>`\nError: {e}")

@app.on_message(filters.command("delvip") & filters.user(ADMIN_ID))
async def del_vip_cmd(_, message: Message):
    try:
        target_id = str(message.command[1])
        if target_id in db["vips"]:
            del db["vips"][target_id]
            save_db(db)
            await message.reply_text(f" User `{target_id}` ၏ VIP အား ပယ်ဖျက်လိုက်ပါပြီ။")
        else:
            await message.reply_text(" ထို ID သည် VIP စာရင်းတွင် မရှိပါ။")
    except Exception as e:
        await message.reply_text(f" Syntax: `/delvip <user_id>`")

async def main():
    await app.start()
    await call_py.start()
    print(" Music VIP Bot Is Successfully Running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

