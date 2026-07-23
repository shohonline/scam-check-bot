import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiohttp import web
import sqlite3
import re
import pytesseract
from PIL import Image
import io

# ⚙️ SOZLAMALAR
API_TOKEN = os.getenv("BOT_TOKEN", "8848826031:AAFRMSjkV2ON9YzqAuIslOeyfux71UjFSls")
ADMIN_ID = int(os.getenv("ADMIN_ID", "277126097"))

# Tesseract o'rnatilgan joyi (Renderda odatda shunday bo'ladi)
# Agar mahalliy kompyuterda ishlatayotgan bo'lsangiz, yo'lni o'zgartirishingiz mumkin:
# Masalan: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Agar apt.yml orqali o'rnatilsa, bu qator shart bo'lmasligi ham mumkin, lekin qo'shib qo'yish zarar qilmaydi.

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 🗄 BAZA BILAN ISHLASH (SQLite)
def init_db():
    conn = sqlite3.connect("fraud_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frauds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT UNIQUE,
            reason TEXT,
            type TEXT  -- 'card', 'phone', 'link' kabi turlarni saqlash uchun
        )
    """)
    conn.commit()
    conn.close()

init_db()

def add_to_db(target, reason, fraud_type):
    conn = sqlite3.connect("fraud_database.db")
    cursor = conn.cursor()
    try:
        # Tozalangan targetni saqlaymiz (faqat raqamlar/standart link)
        cursor.execute("INSERT OR REPLACE INTO frauds (target, reason, type) VALUES (?, ?, ?)", (target, reason, fraud_type))
        conn.commit()
        success = True
    except Exception as e:
        logging.error(f"DB Error: {e}")
        success = False
    conn.close()
    return success

def check_in_db(target):
    conn = sqlite3.connect("fraud_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT reason, type FROM frauds WHERE target = ?", (target,))
    result = cursor.fetchone()
    conn.close()
    return result if result else None

# 🔍 REGEX PATTERNS (Izlash uchun qoliplar)
# Karta: 16 ta raqam (orasida probel yoki tire bo'lishi mumkin)
CARD_REGEX = r'\b(?:\d[ -]*?){16}\b'
# Telefon: O'zbekiston nomeri +998 bilan yoki 9 talik
PHONE_REGEX = r'(?:\+?998|0)[ -]*?[1-9][0-9][ -]*?[0-9][0-9][ -]*?[0-9][0-9][ -]*?[0-9][0-9]'
# Havola: http, https yoki t.me
LINK_REGEX = r'(https?://[^\s]+|t\.me/[^\s]+)'

def clean_text(text):
    # Barcha probel va tirelarni olib tashlaymiz
    return re.sub(r'[\s-]', '', text)

def analyze_text_for_frauds(text):
    raw_text = text
    cleaned = clean_text(text)
    
    found_items = []
    
    # Kartalarni qidirish
    cards = re.findall(CARD_REGEX, cleaned)
    for card in cards:
        if len(card) == 16: # Tekshirish
            db_result = check_in_db(card)
            found_items.append({'value': card, 'type': '❌ Karta', 'info': db_result})

    # Telefonlarni qidirish
    phones = re.findall(PHONE_REGEX, cleaned)
    for phone in phones:
        cl_phone = clean_text(phone)
        # Nomer standartlash (+998 bilan boshlash)
        if not cl_phone.startswith('+998') and len(cl_phone) == 12:
             cl_phone = '+' + cl_phone
        db_result = check_in_db(cl_phone)
        found_items.append({'value': cl_phone, 'type': '📞 Telefon', 'info': db_result})

    # Havolalarni qidirish
    links = re.findall(LINK_REGEX, raw_text) # Havolalarni tozalash shart emas
    for link in links:
        db_result = check_in_db(link)
        found_items.append({'value': link, 'info': db_result})

    return found_items

# OCR Funksiyasi
async def ocr_image(file_id):
    try:
        # Rasmni Telegramdan yuklab olamiz
        file = await bot.get_file(file_id)
        file_path = file.file_path
        image_data = await bot.download_file(file_path)
        
        # PImaginga ochamiz
        image = Image.open(image_data)
        
        # OCR orqali matnni o'qiymiz (rus va ingliz tillarini qo'llab-quvvatlaymiz, yaxshiroq o'qishi uchun)
        # Eslatma: Rus va ingliz tillari Tesseractga oldindan o'rnatilgan bo'lishi kerak (apt.yml buni qiladi)
        text = pytesseract.image_to_string(image, lang='rus+eng')
        
        return text
    except Exception as e:
        logging.error(f"OCR Error: {e}")
        return None

# Web Server (Render uchun)
async def handle(request):
    return web.Response(text="Bot is running with OCR!")

app = web.Application()
app.router.add_get('/', handle)

# MENYU
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Tekshirish")
    builder.button(text="⚠️ Shikoyat yuborish")
    builder.button(text="ℹ️ Oferta va Qoidalar")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    oferta_text = (
        "👋 **SCAM CHECK botiga xush kelibsiz!**\n\n"
        "🤖 **Botning vazifasi:**\n"
        "Ushbu bot internetdagi firibgarlarni aniqlash, shubhali hamyonlar, bank kartalari, "
        "telefon raqamlari va **havolalarni** oldindan tekshirish hamda xavfsiz muhit yaratish uchun xizmat qiladi.\n\n"
        "🆕 **YANGILIK:** Bot endi **Skrinshotlarni ham tahlil qila oladi!** "
        "Shunchaki to'lov cheki yoki yozishma skrinshotini yuboring, biz undagi ma'lumotlarni avtomatik tekshiramiz.\n\n"
        "⚖️ **OMMAVIY OFERTA:** Tizim ma'lumotlarning 100% to'g'riligiga kafolat bermaydi. Yakuniy qaror **foydalanuvchining** o'zida qoladi.\n\n"
        "👉 Botdan foydalanish orqali siz ushbu shartlarga rozilik bildirasiz."
    )
    await message.reply(oferta_text, parse_mode="Markdown", reply_markup=main_menu())

@dp.message(F.text == "ℹ️ Oferta va Qoidalar")
async def show_oferta(message: types.Message):
    await message.reply(
        "📜 **Botdan foydalanish qoidalari:**\n\n"
        "1️⃣ Asossiz shikoyat yuborish va asossiz tuhmat qilish qat'iyan taqiqlanadi.\n"
        "2️⃣ Har bir yuborilgan ariza ma'murlar tomonidan chek va skrinshotlar orqali tekshiriladi.\n"
        "3️⃣ Tizim orqali qidirilgan ma'lumotlar faqat **foydalanuvchi** xavfsizligi uchun ko'rsatiladi.\n"
        "4️⃣ Bot hech qachon shaxsiy ma'lumotlarni ommaga oshkor qilmaydi.",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🔍 Tekshirish")
async def ask_for_check(message: types.Message):
    await message.reply(
        "📋 **TEKSHIRISH BO'YICHA YO'RIQNOMA:**\n\n"
        "Sotuvchi yoki xizmat ko'rsatuvchini tekshirish uchun quyidagilardan birini botga yuboring:\n\n"
        "➡️ **1-usul:** Telefon raqamini yozing (Masalan: `+998901234567`)\n"
        "➡️ **2-usul:** Plastik karta raqamini yozing (Masalan: `8600123456789012`)\n"
        "➡️ **3-usul:** Gumonlanuvchining Telegram profilidan bitta xabarni botga **Forward (Uzatish)** qiling.\n"
        "➡️ **🆕 4-usul:** To'lov cheki yoki yozishma aks etgan **Rasm (Skrinshot)** yuboring.\n\n"
        "✍️ *Hozirning o'zida ma'lumotni shu yerga yuboring:*",
        parse_mode="Markdown"
    )

@dp.message(F.text == "⚠️ Shikoyat yuborish")
async def ask_for_report(message: types.Message):
    await message.reply(
        "📣 **SHIKOYAT YUBORISH YO'RIQNOMASI:**\n\n"
        "Agar siz firibgarlik qurboni bo'lgan bo'lsangiz yoki shubhali shaxsga duch kelsangiz, ariza qoldiring. "
        "Arizangiz ma'murlar bazasiga qo'shilishi uchun quyidagi ma'lumotlarni taqdim etishingiz shart:\n\n"
        "1️⃣ Firibgarning aniq telefon raqami yoki bank kartasi raqami (izohda yozib qoldiring).\n"
        "2️⃣ Pul o'tkazilganligini isbotlovchi **to'lov cheki (kvitansiya)** yoki **skrinshot** rasmi.\n\n"
        "📩 *Ushbu rasm va ma'lumotlarni bitta xabarga yig'ib, rasm ko'rinishida yuboring (rasm ostiga karta yoki tel raqamni yozib qoldiring).*",
        parse_mode="Markdown"
    )

# Rasm kelganda ishlaydigan funksiya (ham shikoyat, ham tekshirish uchun)
@dp.message(F.photo)
async def handle_photo_input(message: types.Message):
    # 1. OCR orqali matnni o'qiymiz
    status_msg = await message.reply("⏳ Rasm tahlil qilinmoqda (OCR)... Bu biroz vaqt olishi mumkin.")
    photo_file_id = message.photo[-1].file_id
    ocr_text = await ocr_image(photo_file_id)
    
    if not ocr_text:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="❌ Rasmdan matn o'qib bo'lmadi. Iltimos, tiniqroq rasm yuboring yoki matn/forward qiling.")
        return

    # 2. Matnni tahlil qilib, shubhali ma'lumotlarni ajratamiz
    fraud_analysis = analyze_text_for_frauds(ocr_text)
    
    await bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

    # 3. Natijalarni ko'rsatamiz
    if fraud_analysis:
        response_text = "🚨 **SKRINSHOT TAHLILI NATIJASI:**\n\n"
        found_fraud = False
        
        # Tekshirilgan elementlar bo'yicha javob tuzamiz
        checked_values = set() # Takrorlanmaslik uchun
        
        for item in fraud_analysis:
            if item['value'] in checked_values: continue
            checked_values.add(item['value'])
            
            if item['info']:
                response_text += f"{item['type']}: `{item['value']}` -> ⚠️ **BAZADA BOR!** {item['info'][0]}\n"
                found_fraud = True
            else:
                # Agar bazada topilmasa, odatda uni shubhali deb belgilash shart emas. 
                # Lekin biz hamma topilgan narsani ko'rsatamiz shaffoflik uchun.
                response_text += f"{item['type']}: `{item['value']}` -> ✅ Bazada topilmadi.\n"
                
        if not found_fraud:
             response_text += "\n✅ Rasmda aniqlangan ma'lumotlar bazamizdagi ma'lum qora ro'yxat bilan mos kelmadi. Har doim hushyor bo'ling!"

        response_text += "\n⚠️ *Eslatma: Bu avtomatlashtirilgan tahlil. Yakuniy qaror o'zingizga bog'liq.*"
        
    else:
        response_text = "✅ Rasm t
