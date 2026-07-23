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

# ⚙️ SOZLAMALAR
API_TOKEN = os.getenv("BOT_TOKEN", "8848826031:AAFRMSjkV2ON9YzqAuIslOeyfux71UjFSls")
ADMIN_ID = int(os.getenv("ADMIN_ID", "277126097"))

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
            type TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def add_to_db(target, reason, fraud_type="general"):
    conn = sqlite3.connect("fraud_database.db")
    cursor = conn.cursor()
    try:
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

# 🔍 REGEX PATTERNS
CARD_REGEX = r'\b(?:\d[ -]*?){16}\b'
PHONE_REGEX = r'(?:\+?998|0)[ -]*?[1-9][0-9][ -]*?[0-9][0-9][ -]*?[0-9][0-9][ -]*?[0-9][0-9]'
LINK_REGEX = r'(https?://[^\s]+|t\.me/[^\s]+)'

def clean_text(text):
    return re.sub(r'[\s-]', '', text)

def analyze_text_for_frauds(text):
    raw_text = text
    cleaned = clean_text(text)
    found_items = []
    
    cards = re.findall(CARD_REGEX, cleaned)
    for card in cards:
        if len(card) == 16:
            db_result = check_in_db(card)
            found_items.append({'value': card, 'type': 'Karta', 'info': db_result})

    phones = re.findall(PHONE_REGEX, cleaned)
    for phone in phones:
        cl_phone = clean_text(phone)
        if not cl_phone.startswith('+998') and len(cl_phone) == 12:
             cl_phone = '+' + cl_phone
        db_result = check_in_db(cl_phone)
        found_items.append({'value': cl_phone, 'type': 'Telefon', 'info': db_result})

    links = re.findall(LINK_REGEX, raw_text)
    for link in links:
        db_result = check_in_db(link)
        found_items.append({'value': link, 'type': 'Havola', 'info': db_result})

    return found_items

# OCR Funksiyasi
async def ocr_image(file_id):
    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
        image_data = await bot.download_file(file_path)
        image = Image.open(image_data)
        text = pytesseract.image_to_string(image, lang='rus+eng')
        return text
    except Exception as e:
        logging.error(f"OCR Error: {e}")
        return None

async def handle(request):
    return web.Response(text="Bot is running with OCR!")

app = web.Application()
app.router.add_get('/', handle)

def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Tekshirish")
    builder.button(text="Shikoyat yuborish")
    builder.button(text="Oferta va Qoidalar")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    oferta_text = (
        "SCAM CHECK botiga xush kelibsiz!\n\n"
        "Botning vazifasi:\n"
        "Ushbu bot internetdagi firibgarlarni aniqlash, shubhali hamyonlar, bank kartalari, "
        "telefon raqamlari va havolalarni oldindan tekshirish uchun xizmat qiladi.\n\n"
        "OMMAVIY OFERTA: Tizim ma'lumotlarning 100% to'g'riligiga kafolat bermaydi."
    )
    await message.reply(oferta_text, reply_markup=main_menu())

@dp.message(F.text == "Oferta va Qoidalar")
async def show_oferta(message: types.Message):
    await message.reply(
        "Botdan foydalanish qoidalari:\n\n"
        "1. Asossiz shikoyat yuborish taqiqlanadi.\n"
        "2. Har bir ariza ma'murlar tomonidan tekshiriladi."
    )

@dp.message(F.text == "Tekshirish")
async def ask_for_check(message: types.Message):
    await message.reply(
        "Tekshirish uchun quyidagilardan birini yuboring:\n\n"
        "- Telefon raqami, karta raqami yoki havola\n"
        "- Yoki to'lov cheki / skrinshot rasm"
    )

@dp.message(F.text == "Shikoyat yuborish")
async def ask_for_report(message: types.Message):
    await message.reply(
        "Shikoyat yuborish uchun shubhali karta, telefon raqam yoki havolani hamda isbotlovchi rasmni birga yuboring."
    )

@dp.message(F.photo)
async def handle_photo_input(message: types.Message):
    status_msg = await message.reply("Rasm tahlil qilinmoqda (OCR)... Kuting.")
    photo_file_id = message.photo[-1].file_id
    ocr_text = await ocr_image(photo_file_id)
    
    if not ocr_text:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="Rasmdan matn o'qib bo'lmadi.")
        return

    fraud_analysis = analyze_text_for_frauds(ocr_text)
    await bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

    user_text = message.caption if message.caption else "Izoh yozilmagan"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Tasdiqlash va bazaga qo'shish", callback_data=f"approve_{message.from_user.id}")
    builder.button(text="Rad etish", callback_data=f"reject_{message.from_user.id}")
    builder.adjust(2)

    # Markdown ishlatilmaydi, oddiy matn formatida yuboriladi
    report_details = (
        "YANGI SKRINSHOT / SHIKOYAT!\n\n"
        f"Yuboruvchi: {message.from_user.full_name}\n"
        f"ID: {message.from_user.id}\n"
        f"Rasm ostidagi izoh: {user_text}\n\n"
        f"OCR topgan matn:\n{ocr_text[:300]}"
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=report_details,
        reply_markup=builder.as_markup()
    )

    response_text = "Rasm qabul qilindi va tahlil qilindi!\n\n"
    if fraud_analysis:
        for item in fraud_analysis:
            if item['info']:
                response_text += f"Topildi ({item['type']}): {item['value']} -> Bazada bor!\n"
            else:
                response_text += f"Aniqlandi ({item['type']}): {item['value']} -> Bazada topilmadi.\n"
    else:
        response_text += "Rasm ichidan aniq karta yoki raqam topilmadi, lekin shikoyat adminga yuborildi."

    await message.reply(response_text)

@dp.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def admin_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Siz admin emassiz!", show_alert=True)
        return

    action, user_id = callback.data.split("_")
    message = callback.message

    if action == "approve":
        add_to_db("Test_Target_From_Photo", "Chek yoki skrinshot asosida tasdiqlandi", "card")
        await callback.message.edit_caption(
            caption=message.caption + "\n\nSTATUS: BAZAGA QO'SHILDI!"
        )
        await callback.answer("Tasdiqlandi va bazaga qo'shildi!")
    else:
        await callback.message.edit_caption(
            caption=message.caption + "\n\nSTATUS: RAD ETILDI!"
        )
        await callback.answer("Rad etildi.")

@dp.message(F.forward_from)
async def check_forwarded_user(message: types.Message):
    tg_id = str(message.forward_from.id)
    res = check_in_db(tg_id)
    if res:
        await message.reply(f"DIQQAT! XAVF:\n{res[0]}")
    else:
        await message.reply("Bu foydalanuvchi qora ro'yxatda yo'q.")

@dp.message(F.text)
async def check_text_input(message: types.Message):
    user_input = message.text.strip().replace(" ", "")
    if user_input in ["Tekshirish", "Shikoyatyuborish", "OfertavaQoidalar"]:
        return

    res = check_in_db(user_input)
    if res:
        await message.reply(f"DIQQAT! BAZADA TOPILDI:\n{res[0]}")
    else:
        await message.reply("Bu ma'lumot bazamizda topilmadi. Hushyor bo'ling!")

async def start_bot():
    await dp.start_polling(bot)

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    await start_bot()

if __name__ == '__main__':
    asyncio.run(main())
