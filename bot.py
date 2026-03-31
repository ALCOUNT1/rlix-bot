import telebot
from telebot import types
import pyotp
import time
from flask import Flask, request
from datetime import datetime, timedelta
from collections import defaultdict

# ==========================================
# --- [1] إعدادات الربط والاستقرار (Webhook) ---
# ==========================================
API_TOKEN = '7696920225:AAH65z3y6eJv5dmquqgHsrdQLR2ubfv5QoI'
USERNAME = 'ALCOUNT' 
SECRET_GATE = 'rlix_v94_stable_gate'

bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

# --- بيانات المتجر والحسابات (التي أرسلتها) ---
GAME_ACCOUNTS = {
    "GHOST OF YOTEI": {
        "email": "rlixstore902@gmail.com", 
        "pass": "RLIX08731",
        "keywords": ["ghost", "yotei", "قوست", "شبح"]
    }
}

URLS = {
    "store": "https://rlix-store.com/ar",
    "subscriptions": "https://rlix-store.com/subscriptions",
    "games": "https://rlix-store.com/games",
    "offers": "https://rlix-store.com/offers",
    "new": "https://rlix-store.com/new-products",
    "psn_guide": "https://rlix-store.com/pages/psn-activation-guide"
}

FIXED_PSN_SECRET = 'TTJA4MHGR4UOA3SHBY5M255TJBAYVMCAXYNNW672OQAL42PTZVMXL4EUFPAUITBGTXLVEA5YRMBYTNM7GKLTPNN454HUL2YVCGC557I'
WHATSAPP_SUPPORT = "https://wa.me/966507044561"
TELEGRAM_SUPPORT = "https://t.me/RlixSupport"

user_temp = defaultdict(lambda: {'state': 'idle', 'platform': None, 'order_id': None, 'game_input': None})
banned_users = {}

# ==========================================
# --- [2] محرك الاستقبال (Flask Routes) ---
# ==========================================

@app.route('/' + SECRET_GATE, methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    return "Forbidden", 403

@app.route('/')
def setup():
    webhook_url = f"https://{USERNAME}.pythonanywhere.com/{SECRET_GATE}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    return "<h1>RLIX V94.2: SYSTEM ACTIVE ✅</h1>", 200

# ==========================================
# --- [3] لوحات المفاتيح (Keyboards) ---
# ==========================================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🔑 الحصول على كود التحقق"), types.KeyboardButton("📦 تصفح المنتجات"))
    return markup

# ==========================================
# --- [4] معالجة الرسائل والبحث الذكي ---
# ==========================================

@bot.message_handler(commands=['start', 'clear'])
def send_welcome(message):
    user_temp[message.chat.id] = {'state': 'idle'}
    welcome_text = (
        "👋 **مرحباً بك في بوت متجر رليكس!**\n\n"
        "📖 **كيفية الاستخدام:**\n\n"
        "1️⃣ اضغط على زر 'الحصول على كود التحقق'.\n"
        "2️⃣ أدخل رقم الطلب والبيانات المطلوبة.\n"
        "3️⃣ اقرأ طريقة التفعيل ووافق على الشروط.\n"
        "4️⃣ استلم الكود والبيانات فوراً.\n"
        "5️⃣ يمكنك إرسال كلمة **'دعم'** للحصول على مساعدة فورية."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if text == "🔑 الحصول على كود التحقق":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔢 طلب كود بلاستيشن (OTP)", callback_data="get_psn_otp"))
        bot.send_message(chat_id, "🎯 **نظام استخراج الأكواد:**\nأرسل اسم اللعبة للبحث عن بيانات الحساب:", reply_markup=markup, parse_mode='Markdown')
        user_temp[chat_id]['state'] = 'searching_game'
        
    elif text == "دعم":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 واتساب", url=WHATSAPP_SUPPORT),
                   types.InlineKeyboardButton("✈️ تيليجرام", url=TELEGRAM_SUPPORT))
        bot.send_message(chat_id, "🛠️ **الدعم الفني:**", reply_markup=markup, parse_mode='Markdown')

    elif user_temp[chat_id]['state'] == 'searching_game':
        found = False
        for name, data in GAME_ACCOUNTS.items():
            if name.lower() in text.lower() or any(k in text.lower() for k in data['keywords']):
                res = (f"✅ **تم العثور على اللعبة:**\n\n"
                       f"🎮 `{name}`\n"
                       f"📧 الإيميل: `{data['email']}`\n"
                       f"🔑 الباسورد: `{data['pass']}`")
                bot.send_message(chat_id, res, parse_mode='Markdown')
                found = True
                break
        if not found:
            bot.send_message(chat_id, "❌ لم يتم العثور على اللعبة في المخزون حالياً.")

# ==========================================
# --- [5] استخراج كود PSN (العد التنازلي) ---
# ==========================================

@bot.callback_query_handler(func=lambda call: True)
def handle_clicks(call):
    chat_id = call.message.chat.id
    
    if call.data == "get_psn_otp":
        counter = bot.send_message(chat_id, "🔍 جاري بدء الفحص المزدوج...")
        for i in range(1, 6):
            time.sleep(1)
            try: bot.edit_message_text(f"⏳ جاري سحب الكود... {i}/5", chat_id, counter.message_id)
            except: pass
        
        totp = pyotp.TOTP(FIXED_PSN_SECRET.replace(" ", "").upper())
        bot.delete_message(chat_id, counter.message_id)
        bot.send_message(chat_id, f"✅ **كود بلاستيشن الجديد:**\n\n`{totp.now()}`", parse_mode='Markdown')
