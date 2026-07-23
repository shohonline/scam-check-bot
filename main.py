import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiohttp import web
import sqlite3

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
    # Ma'lumotlar bazasi jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frauds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT UNIQUE,
            reason TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def add_to_db(target, reason):
    conn = sqlite3.connect("fraud_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO frauds (target, reason) VALUES (?, ?)", (target, reason))
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
    cursor.execute("SELECT reason FROM frauds WHERE target = ?", (target,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Render port xatosi bermasligi uchun sodda Web Server
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

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
        "Ushbu bot internetdagi firibgarlarni aniqlash, shubhali hamyonlar, bank kartalari "
        "va telefon raqamlarini oldindan tekshirish hamda xavfsiz muhit yaratish uchun xizmat qiladi.\n\n"
        "🤝 **XALQONA CHORLOV:**\n"
        "**Agar siz biror shubhali bank kartasi yoki telefon raqamini bilsangiz, darhol ushbu botga kiriting!** "
        "O'z vaqtida yuborilgan ma'lumotingiz bilan boshqa ko'plab insonlarni firibgarlar tuzog'idan asrab qolgan "
        "va yaqinlaringizga xavfsiz internet muhitini yaratishda yordam bergan bo'lasiz!\n\n"
        "⚖️ **OMMAVIY OFERTA (DISCLAIMER):**\n"
        "Bot foydalanuvchilar tomonidan yuborilgan shikoyatlar asosida ishlovchi axborot almashish platformasidir. "
        "Tizim ma'lumotlarning 100% to'g'riligiga kafolat bermaydi. Yakuniy qaror **foydalanuvchining** o'zida qoladi.\n\n"
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
        "4️⃣ Bot hech qachon shaxsiy ma'lumotlarni (ism, rasm, yashash manzili) ommaga oshkor qilmaydi.",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🔍 Tekshirish")
async def ask_for_check(message: types.Message):
    await message.reply(
        "📋 **TEKSHIRISH BO'YICHA YO'RIQNOMA:**\n\n"
        "Sotuvchi yoki xizmat ko'rsatuvchini tekshirish uchun quyidagilardan birini botga yuboring:\n\n"
        "➡️ **1-usul:** Sotuvchining telefon raqamini yozing (Masalan: `+998901234567`)\n"
        "➡️ **2-usul:** Plastik karta raqamini yozing (Masalan: `8600123456789012`)\n"
        "➡️ **3-usul:** Gumonlanuvchining Telegram profilidan bitta xabarni ushbu botga **Forward (Uzatish)** qiling.\n\n"
        "✍️ *Hozirning o'zida ma'lumotni shu yerga matn ko'rinishida yozing yoki xabarni uzating:*",
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

@dp.message(F.photo)
async def forward_report_to_admin(message: types.Message):
    user_text = message.caption if message.caption else ""
    if not user_text:
        await message.reply("⚠️ Iltimos, rasm ostiga (caption) shubhali **karta raqami** yoki **telefon raqamini** yozib yuboring!")
        return

    # Admin uchun tasdiqlash inline tugmalari
    builder = InlineKeyboardBuilder()
    # Ma'lumotni bazaga qo'shish uchun maxsus kalit so'z formatida uzatamiz
    builder.button(text="✅ Tasdiqlash va qo'shish", callback_data=f"approve_{message.from_user.id}")
    builder.button(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
    builder.adjust(2)

    report_details = (
        "📣 **YANGI FIRIBGARLIK HAQIDA SHIKOYAT!**\n\n"
        f"👤 **Yuboruvchi:** {message.from_user.full_name}\n"
        f"🆔 **Yuboruvchi ID:** `{message.from_user.id}`\n"
        f"🔗 **Username:** @{message.from_user.username if message.from_user.username else 'Yoʻq'}\n\n"
        f"📝 **Tekshirilishi kerak bo'lgan raqam/karta va izoh:**\n{user_text}"
    )

    # Adminga rasm va tugmani yuboramiz
    await bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=message.photo[-1].file_id, 
        caption=report_details, 
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    
    await message.reply(
        "✅ **Shikoyatingiz va isbotlovchi chek (rasm) qabul qilindi!**\n\n"
        "Ma'murlarimiz tez fursatda tekshirib, ma'lumotni bazaga kiritishadi. Rahmat! 🙏",
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def admin_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Siz admin emassiz!", show_alert=True)
        return

    action, user_id = callback.data.split("_")
    message = callback.message

    if message.caption:
        lines = message.caption.split("\n")
        # Matn ichidan yuborilgan raqam/karta ma'lumotini ajratib olamiz
        target_info = lines[-1].strip()
    else:
        target_info = "Noma'lum"

    if action == "approve":
        # Bazaga qo'shish (oxirgi qatordagi ma'lumotni kalit qilib olamiz)
        add_to_db(target_info, "Foydalanuvchi shikoyati va chek asosida tasdiqlangan.")
        await callback.message.edit_caption(
            caption=message.caption + "\n\n✅ **STATUS: BAZAGA QO'SHILDI VA TASDIQLANDI!**",
            parse_mode="Markdown"
        )
        await callback.answer("Muvaffaqiyatli bazaga qo'shildi!")
    else:
        await callback.message.edit_caption(
            caption=message.caption + "\n\n❌ **STATUS: RAD ETILDI!**",
            parse_mode="Markdown"
        )
        await callback.answer("Shikoyat rad etildi.")

@dp.message(F.forward_from)
async def check_forwarded_user(message: types.Message):
    tg_id = str(message.forward_from.id)
    reason = check_in_db(tg_id)
    if reason:
        await message.reply(
            f"🚨 **DIQQAT! XAVF ANIQLANDI!**\n\n"
            f"Ushbu Telegram ID (`{tg_id}`) bo'yicha bazamizda ma'lumot bor:\n*{reason}*\n\n"
            f"Oldindan pul o'tkazmaslikni tavsiya etamiz!", parse_mode="Markdown"
        )
    else:
        await message.reply(
            f"✅ Ushbu Telegram ID (`{tg_id}`) hozircha qora ro'yxatda mavjud emas.\n"
            f"Har doim hushyor bo'ling!", parse_mode="Markdown"
        )

@dp.message(F.text)
async def check_text_input(message: types.Message):
    user_input = message.text.strip().replace(" ", "")
    
    if user_input in ["🔍Tekshirish", "⚠️Shikoyatyuborish", "ℹ️OfertavaQoidalar"]:
        return

    reason = check_in_db(user_input)
    if reason:
        await message.reply(
            f"🚨 **DIQQAT! SHUBHALI RAQAM/KARTA!**\n\n"
            f"Ushbu ma'lumot bo'yicha bazamizda topildi:\n*{reason}*\n\n"
            f"Firibgarlik qurboni bo'lmaslik uchun ehtiyot bo'ling!", parse_mode="Markdown"
        )
    else:
        await message.reply(
            "✅ **Ushbu ma'lumotlar bazamizda topilmadi.**\n\n"
            "⚠️ *Eslatma:* Bu ma'lumotning bazada yo'qligi u shaxsning 100% xavfsiz ekanligini anglatmaydi. "
            "Har doim hushyor bo'ling!\n\n"
            "💡 **Sizning yordamingiz kerak:**\n"
            "Agar siz ushbu shaxs yoki boshqa shubhali karta/telefon raqami haqida aniq dalillarga ega bo'lsangiz, "
            "uni botimizga shikoyat sifatida yuboring! 🙏", 
            parse_mode="Markdown"
        )

async def start_bot():
    await dp.start_polling(bot)

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000) # Render porti
    await site.start()
    await start_bot()

if __name__ == '__main__':
    asyncio.run(main())
