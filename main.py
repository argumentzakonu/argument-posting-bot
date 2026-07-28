Python
import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

# ----------------- НАЛАШТУВАННЯ -----------------
POSTING_BOT_TOKEN = "8704920529:AAHj2JA5QpiiU16hIoA-gKFLN3o8cVuiLvA"
FEEDBACK_BOT_TOKEN = "8885800194:AAGhqUKiO-kJt6irlx1fMyiN_Rjn17eY2iY"

CHANNEL_ID = "@argumentzakonu"
ADMIN_ID = 630822108

CHANNEL_LINK = "https://t.me/argumentzakonu"
FEEDBACK_LINK = "https://t.me/argumentzakonubot"

SIGNATURE = f"\n\n⚖️ <a href='{CHANNEL_LINK}'>Аргумент Закону</a> | 📩 <a href='{FEEDBACK_LINK}'>Надіслати новину</a>"
# -------------------------------------------------

bot_post = Bot(token=POSTING_BOT_TOKEN)
bot_feed = Bot(token=FEEDBACK_BOT_TOKEN)

dp_post = Dispatcher()
dp_feed = Dispatcher()

users_mapping = {}

# --- БОТ ПУБЛІКАЦІЙ ---
@dp_post.message(CommandStart())
async def start_posting(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👋 **Бот публікацій готовий!**\n\nНадішліть текст або фото для каналу.", parse_mode=ParseMode.MARKDOWN)

@dp_post.message(F.from_user.id == ADMIN_ID, F.text)
async def post_text(message: types.Message):
    full_text = message.text + SIGNATURE
    try:
        await bot_post.send_message(chat_id=CHANNEL_ID, text=full_text, parse_mode=ParseMode.HTML)
        await message.answer("✅ **Опубліковано в канал!**")
    except Exception as e:
        await message.answer(f"❌ Помилка: `{e}`", parse_mode=ParseMode.MARKDOWN)

@dp_post.message(F.from_user.id == ADMIN_ID, F.photo)
async def post_photo(message: types.Message):
    caption = (message.caption or "") + SIGNATURE
    try:
        await bot_post.send_photo(chat_id=CHANNEL_ID, photo=message.photo[-1].file_id, caption=caption, parse_mode=ParseMode.HTML)
        await message.answer("✅ **Фото опубліковано!**")
    except Exception as e:
        await message.answer(f"❌ Помилка: `{e}`", parse_mode=ParseMode.MARKDOWN)

# --- БОТ ЗВОРОТНОГО ЗВ'ЯЗКУ ---
@dp_feed.message(CommandStart())
async def start_feedback(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Вітаю! Надішліть сюди ваше запитання або новину, і ми вам відповімо.")

@dp_feed.message(F.from_user.id == ADMIN_ID, F.reply_to_message)
async def reply_to_user(message: types.Message):
    user_id = users_mapping.get(message.reply_to_message.message_id)
    if user_id:
        try:
            await bot_feed.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            await message.answer("✅ Ваша відповідь надіслана користувачу.")
        except Exception as e:
            await message.answer(f"❌ Не вдалося надіслати: {e}")
    else:
        await message.answer("⚠️ Не вдалося знайти адресата цього повідомлення.")

@dp_feed.message()
async def forward_to_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID or message.from_user.is_bot:
        return
    
    fw = await bot_feed.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    users_mapping[fw.message_id] = message.from_user.id
    await message.answer("Дякуємо! Ваше повідомлення отримано.")

# --- МІНІ-ВЕБСЕРВЕР ДЛЯ РЕНДЕРА (щоб проходити Port Scan) ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)

    # Запускаємо dummy веб-сервер для Render
    await start_web_server()

    # Скидаємо старі вебхуки та завислі повідомлення
    await bot_post.delete_webhook(drop_pending_updates=True)
    await bot_feed.delete_webhook(drop_pending_updates=True)

    await asyncio.gather(
        dp_post.start_polling(bot_post, drop_pending_updates=True),
        dp_feed.start_polling(bot_feed, drop_pending_updates=True)
    )

if __name__ == '__main__':
    asyncio.run(main())
