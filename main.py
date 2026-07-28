import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

# ----------------- НАЛАШТУВАННЯ -----------------
# Ваш токен нового бота для постінгу від BotFather
BOT_TOKEN = os.getenv(
    "BOT_TOKEN", "8704920529:AAHj2JA5QpiiU16hIoA-gKFLN3o8cVuiLvA"
)

# Юзернейм вашого каналу (замініть на реальний юзернейм каналу, якщо він інший)
CHANNEL_ID = os.getenv("CHANNEL_ID", "@argumentzakonu")

# Ваш особистий Telegram ID
ADMIN_ID = int(os.getenv("ADMIN_ID", "630822108"))

# Посилання для підпису
CHANNEL_LINK = "https://t.me/argumentzakonu"
FEEDBACK_LINK = "https://t.me/argumentzakonubot"  # Ваш бот зворотного зв'язку

# Фірмовий підпис із клікабельними посиланнями
SIGNATURE = (
    f"\n\n⚖️ <a href='{CHANNEL_LINK}'>Аргумент Закону</a> | "
    f"📩 <a href='{FEEDBACK_LINK}'>Надіслати новину</a>"
)
# -------------------------------------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: types.Message):
  if message.from_user.id == ADMIN_ID:
    await message.answer(
        "👋 **Бот для публікацій готовий!**\n\n"
        "Надішліть мені будь-який текст або фото — я опублікую це у ваш канал з підписом.",
        parse_mode=ParseMode.MARKDOWN,
    )
  else:
    await message.answer("Доступ обмежено.")


@dp.message(F.from_user.id == ADMIN_ID, F.text)
async def post_text(message: types.Message):
  full_text = message.text + SIGNATURE
  try:
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=full_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    await message.answer("✅ **Текст опубліковано в канал!**")
  except Exception as e:
    await message.answer(f"❌ Помилка: `{e}`", parse_mode=ParseMode.MARKDOWN)


@dp.message(F.from_user.id == ADMIN_ID, F.photo)
async def post_photo(message: types.Message):
  caption = (message.caption or "") + SIGNATURE
  try:
    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=message.photo[-1].file_id,
        caption=caption,
        parse_mode=ParseMode.HTML,
    )
    await message.answer("✅ **Фото опубліковано!**")
  except Exception as e:
    await message.answer(f"❌ Помилка: `{e}`", parse_mode=ParseMode.MARKDOWN)


async def main():
  logging.basicConfig(level=logging.INFO)
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
