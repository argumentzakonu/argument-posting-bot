import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ----------------- НАЛАШТУВАННЯ -----------------
POSTING_BOT_TOKEN = "8704920529:AAHj2JA5QpiiU16hIoA-gKFLN3o8cVuiLvA"
FEEDBACK_BOT_TOKEN = "8885800194:AAGhqUKiO-kJt6irlx1fMyiN_Rjn17eY2iY"

CHANNEL_ID = "@argumentzakonu"
ADMIN_ID = 630822108

FEEDBACK_LINK = "https://t.me/argumentzakonubot"

# Підпис з терезами та жирним посиланням
SIGNATURE = f"\n\n⚖️ <b><a href='{FEEDBACK_LINK}'>Надіслати новину</a></b>"
# -------------------------------------------------

bot_post = Bot(token=POSTING_BOT_TOKEN)
bot_feed = Bot(token=FEEDBACK_BOT_TOKEN)

dp_post = Dispatcher()
dp_feed = Dispatcher()


# Стан для очікування відповіді адміна
class AdminReply(StatesGroup):
  waiting_for_text = State()


# --- БОТ ПУБЛІКАЦІЙ ---
@dp_post.message(CommandStart())
async def start_posting(message: types.Message):
  if message.from_user.id == ADMIN_ID:
    await message.answer(
        "👋 **Бот публікацій готовий!**\n\nНадішліть текст або фото для каналу.",
        parse_mode=ParseMode.MARKDOWN,
    )


@dp_post.message(F.from_user.id == ADMIN_ID, F.text)
async def post_text(message: types.Message):
  full_text = message.text + SIGNATURE
  try:
    await bot_post.send_message(
        chat_id=CHANNEL_ID,
        text=full_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    await message.answer("✅ **Опубліковано в канал!**")
  except Exception as e:
    await message.answer(f"❌ Помилка: `{e}`", parse_mode=ParseMode.MARKDOWN)


@dp_post.message(F.from_user.id == ADMIN_ID, F.photo)
async def post_photo(message: types.Message):
  caption = (message.caption or "") + SIGNATURE
  try:
    await bot_post.send_photo(
        chat_id=CHANNEL_ID,
        photo=message.photo[-1].file_id,
        caption=caption,
        parse_mode=ParseMode.HTML,
    )
    await message.answer("✅ **Фото опубліковано!**")
  except Exception as e:
    await message.answer(f"❌ Помилка: `{e}`", parse_mode=ParseMode.MARKDOWN)


# --- БОТ ЗВОРОТНОГО ЗВ'ЯЗКУ ---
@dp_feed.message(CommandStart())
async def start_feedback(message: types.Message):
  if message.from_user.id != ADMIN_ID:
    await message.answer(
        "Вітаю! Надішліть сюди ваше запитання або новину, і ми вам відповімо."
    )


# Кнопка "💬 Надати відповідь"
@dp_feed.callback_query(F.data.startswith("reply_"))
async def cb_reply(call: types.CallbackQuery, state: FSMContext):
  user_id = call.data.split("_")[1]
  await state.update_data(target_user_id=user_id)
  await state.set_state(AdminReply.waiting_for_text)

  await call.message.answer(
      f"✍️ **Введіть текст відповіді для користувача (ID: {user_id}):**",
      parse_mode=ParseMode.MARKDOWN,
  )
  await call.answer()


# Надсилання відповіді користувачу від адміна
@dp_feed.message(AdminReply.waiting_for_text, F.from_user.id == ADMIN_ID)
async def send_reply_to_user(message: types.Message, state: FSMContext):
  data = await state.get_data()
  user_id = data.get("target_user_id")

  try:
    await bot_feed.copy_message(
        chat_id=user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    await message.answer("✅ Ваша відповідь успішно надіслана користувачу!")
  except Exception as e:
    await message.answer(f"❌ Помилка надсилання: {e}")

  await state.clear()


# Отримання повідомлення від користувача (мовчки, без автовідповіді)
@dp_feed.message()
async def forward_to_admin(message: types.Message, state: FSMContext):
  if message.from_user.id == ADMIN_ID or message.from_user.is_bot:
    return

  user = message.from_user
  user_info = f"{user.full_name}" + (
      f" (@{user.username})" if user.username else ""
  )

  kb = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="💬 Надати відповідь", callback_data=f"reply_{user.id}"
          )
      ]]
  )

  await bot_feed.send_message(
      chat_id=ADMIN_ID,
      text=f"📩 **Повідомлення від {user_info} (ID: `{user.id}`):**",
      parse_mode=ParseMode.MARKDOWN,
  )
  await bot_feed.copy_message(
      chat_id=ADMIN_ID,
      from_chat_id=message.chat.id,
      message_id=message.message_id,
      reply_markup=kb,
  )


# --- МІНІ-ВЕБСЕРВЕР ДЛЯ РЕНДЕРА ---
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
  await start_web_server()

  await asyncio.gather(
      dp_post.start_polling(bot_post), dp_feed.start_polling(bot_feed)
  )


if __name__ == "__main__":
  asyncio.run(main())
