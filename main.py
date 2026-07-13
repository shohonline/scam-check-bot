import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import asyncio

# ⚙️ TOKЕN VA ADMIN ID SIZNING MA'LUMOTLARINGIZGA SOZLANDI
API_TOKEN = '8848826031:AAFRMSjkV2ON9YzqAuIslOeyfux71UjFSls'
ADMIN_ID = 277126097  

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 📊 Sinov uchun boshlang'ich qora ro'yxat bazasi
FRAUD_DATABASE = {
    "+998901234567": "shubhali faoliyat bo'yicha 3 ta shikoyat bor.",
    "8600123456789012": "firibgarlik isboti (chek) mavjud.",
    "277126097": "test rejimi: bu sizning ID raqamingiz."
}

# 1. SODDA FOYDALANUVChI INТERFEYSI (MENYU)
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Tekshirish")
    builder.button(text="⚠️ Shikoyat yuborish")
    builder.button(text="ℹ️ Oferta va Qoidalar")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

# 2. START BOSILGANDA OFERTA BILAN KUTIB OLISh
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    oferta_text = (
        "👋 **SCAM CHECK botiga xush kelibsiz!**\n\n"
        "⚖️ **OMMAVIY OFERTA (DISCLAIMER):**\n"
        "Ushbu bot foydalanuvchilar tomonidan yuborilgan shikoyatlar asosida ishlovchi "
        "axborot almashish platformasidir. Bot ma'lumotlarning 100% to'g'riligiga kafolat bermaydi. "
        "Tizim faqat ogohlantirish xarakteriga ega va yakuniy qaror xaridorning o'zida qoladi.\n\n"
        "👉 Botdan foydalanish orqali siz ushbu shartlarga rozilik bildirasiz."
    )
    await message.reply(oferta_text, parse_mode="Markdown", reply_markup=main_menu())

# 3. QONUNIY OFERTA MATNI
@dp.message(F.text == "ℹ️ Oferta va Qoidalar")
async def show_oferta(message: types.Message):
    await message.reply(
        "📜 **Bot Qoidalari:**\n"
        "1. Asossiz shikoyat yuborish va birovga tuhmat qilish taqiqlanadi.\n"
        "2. Har bir shikoyat ma'murlar tomonidan chek va skrinshotlar orqali tekshiriladi.\n"
        "3. Bot shaxsiy ma'lumotlarni (ism, rasm, manzil) ommaga oshkor qilmaydi.",
        parse_mode="Markdown"
    )

# 4. TEKSHIRISH TUGMASI BOSILGANDA
@dp.message(F.text == "🔍 Tekshirish")
async def ask_for_check(message: types.Message):
    await message.reply(
        "✍️ Sotuvchining **Telefon raqamini**, **Bank karta raqamini** yozing yoki "
        "uning profilidan biror xabarni shu yerga **Forward (Uzatish)** qiling:"
    )

# 5. SHIKOYAT YUBORISH TUGMASI BOSILGANDA
@dp.message(F.text == "⚠️ Shikoyat yuborish")
async def ask_for_report(message: types.Message):
    await message.reply(
        "📣 Shikoyat yuborish uchun firibgarning raqamini/kartasini yozing, "
        "yozishmalar skrinshoti va to'lov chekini (kvitansiya) rasm holatida yuboring.\n\n"
        "Arizangiz ma'murlar tomonidan tekshirilib, bazaga qo'shiladi."
    )

# 6. FORWARD (UZATISH) ORQALI TELEGRAM ID'SINI TEKSHIRISH (O'ZGARMAYDIGAN ID)
@dp.message(F.forward_from)
async def check_forwarded_user(message: types.Message):
    tg_id = str(message.forward_from.id)
    
    if tg_id in FRAUD_DATABASE:
        await message.reply(
            f"🚨 **DIQQAT! XAVF ANIQLANDI!**\n\n"
            f"Ushbu Telegram ID (`{tg_id}`) bo'yicha bazamizda: *{FRAUD_DATABASE[tg_id]}* "
            f"Oldindan pul o'tkazmaslikni tavsiya etamiz!", parse_mode="Markdown"
        )
    else:
        await message.reply(
            f"✅ Ushbu Telegram ID (`{tg_id}`) hozircha qora ro'yxatda mavjud emas.\n"
            f"Har doim hushyor bo'ling!", parse_mode="Markdown"
        )

# 7. MATNLI QIDIRUV (TELEFON RAQAM, KARTA YOKI ID RAQAM)
@dp.message(F.text)
async def check_text_input(message: types.Message):
    user_input = message.text.strip().replace(" ", "")
    
    if user_input in ["🔍Tekshirish", "⚠️Shikoyatyuborish", "ℹ️OfertavaQoidalar"]:
        return

    if user_input in FRAUD_DATABASE:
        await message.reply(
            f"🚨 **DIQQAT! SHUBHALI RAQAM/KARTA/ID!**\n\n"
            f"Ushbu ma'lumot bo'yicha bazamizda: *{FRAUD_DATABASE[user_input]}*\n"
            f"Firibgarlik qurboni bo'lmaslik uchun ehtiyot bo'ling!", parse_mode="Markdown"
        )
    else:
        await message.reply(
            "✅ Ushbu ma'lumotlar bazamizda topilmadi.\n\n"
            "⚠️ Eslatma: Bu uning 100% xavfsiz ekanligini anglatmaydi. "
            "To'lov qilishdan oldin har tomonlama tekshiring!"
        )

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
