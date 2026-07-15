import os  # Muhit o'zgaruvchilari bilan ishlash uchun qo'shildi
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import asyncio
from aiohttp import web  # Render uchun veb-server

# ⚙️ SOZLAMALAR (XAVFSIZ USUL)
# Render platformasida BOT_TOKEN va ADMIN_ID o'zgaruvchilari kiritilsa, ulardan foydalanadi.
# Agar kiritilmasa, quyidagi zaxira qiymatlarni ishlatadi.
API_TOKEN = os.getenv("BOT_TOKEN", "8848826031:AAFRMSjkV2ON9YzqAuIslOeyfux71UjFSls")
ADMIN_ID = int(os.getenv("ADMIN_ID", "277126097"))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Vaqtincha test bazasi (Kalit so'zlar probelsiz yozilishi shart)
FRAUD_DATABASE = {
    "+998901234567": "shubhali faoliyat bo'yicha 3 ta shikoyat bor.",
    "8600123456789012": "firibgarlik isboti (chek) mavjud.",
    "277126097": "test rejimi: bu sizning ID raqamingiz."
}

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
        "1️⃣ Firibgarning aniq telefon raqami yoki bank kartasi raqami.\n"
        "2️⃣ Pul o'tkazilganligini isbotlovchi **to'lov cheki (kvitansiya)** rasmi.\n"
        "3️⃣ Aldov yoki yozishmalar aks etgan **skrinshotlar**.\n\n"
        "📩 *Ushbu barcha isbotlarni bitta xabarga yig'ib, rasm holatida shu yerga yuboring. Ma'murlarimiz tez fursatda ko'rib chiqishadi.*",
        parse_mode="Markdown"
    )

@dp.message(F.photo)
async def forward_report_to_admin(message: types.Message):
    user_text = message.caption if message.caption else "Izoh qoldirilmagan."
    report_details = (
        "📣 **YANGI FIRIBGARLIK HAQIDA SHIKOYAT!**\n\n"
        f"👤 **Yuboruvchi:** {message.from_user.full_name}\n"
        f"🆔 **Yuboruvchi ID:** `{message.from_user.id}`\n"
        f"🔗 **Username:** @{message.from_user.username if message.from_user.username else 'Yoʻq'}\n\n"
        f"📝 **Kelgan ma'lumot va izoh:**\n{user_text}"
    )
    await bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=message.photo[-1].file_id, 
        caption=report_details, 
        parse_mode="Markdown"
    )
    await message.reply(
        "✅ **Shikoyatingiz va isbotlovchi chek (rasm) qabul qilindi!**\n\n"
        "Ma'murlarimiz ma'lumotlarni tekshirib chiqqach, ushbu shaxsni qora ro'yxatga qo'shishadi. "
        "Jamiyatimiz xavfsizligiga hissa qo'shganingiz uchun rahmat! 🙏",
        parse_mode="Markdown"
    )

@dp.message(F.forward_from)
async def check_forwarded_user(message: types.Message):
    tg_id = str(message.forward_from.id)
    if tg_id in FRAUD_DATABASE:
        await message.reply(
            f"🚨 **DIQQAT! XAVF ANIQLANDI!**\n\n"
            f"Ushbu Telegram ID (`{tg_id}`) bo'yicha bazamizda: *{FRAUD_DATABASE[tg_id]}*\n"
            f"Oldindan pul o'tkazmaslikni tavsiya etamiz!", parse_mode="Markdown"
        )
    else:
        await message.reply(
            f"✅ Ushbu Telegram ID (`{tg_id}`) hozircha qora ro'yxatda mavjud emas.\n"
            f"Har doim hushyor bo'ling!", parse_mode="Markdown"
        )

@dp.message(F.forward_date & ~F.forward_from)
async def check_hidden_forward(message: types.Message):
    await message.reply(
        "⚠️ **Xavfsizlik tizimi ogohlantiradi:**\n"
        "Ushbu foydalanuvchi o'z maxfiylik sozlamalarida xabarlarni uzatishni (Forward) yopib qo'ygan. "
        "Shu sababli uning ID raqamini aniqlab bo'lmadi.\n\n"
        "ℹ️ *Tavsiya:* Undan telefon raqami yoki karta raqamini so'rab, shu yerda matn ko'rinishida tekshirib ko'ring."
    )

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
            "✅ **Ushbu ma'lumotlar bazamizda topilmadi.**\n\n"
            "⚠️ *Eslatma:* Bu ma'lumotning bazada yo'qligi u shaxsning 100% xavfsiz ekanligini anglatmaydi. "
            "U yangi firibgarlik hisobini ochgan bo'lishi mumkin. Har doim hushyor bo'ling!\n\n"
            "💡 **Sizning yordamingiz kerak:**\n"
            "Agar siz ushbu shaxs yoki boshqa biron bir shubhali karta/telefon raqami haqida aniq dalillarga ega bo'lsangiz, "
            "uni botimizga kiriting (shikoyat yuboring). Shu orqali yaqinlaringizga va boshqa yurtdoshlarimizga yordam bergan bo'lasiz! 🙏", 
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
