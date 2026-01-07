import os
import asyncio
import logging
from typing import Any, Dict
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация (замените на свои значения)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1090142221  # ID администратора

# Инициализация бота и диспетчера
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Словари с текстами для разных языков
TEXTS = {
    "ru": {
        "start": "Привет! Я бот для обратной связи. Выберите язык:",
        "language_selected": "Язык изменен на русский 🇷🇺",
        "send_feedback": "Отправьте ваш отзыв, вопрос или предложение:",
        "feedback_sent": "✅ Ваше сообщение отправлено администратору!",
        "cancel": "❌ Отменено",
        "new_feedback": "📨 Новое сообщение от пользователя:",
        "user_info": "👤 Пользователь:",
        "reply": "📤 Ответ отправлен пользователю!",
        "error": "❌ Произошла ошибка. Попробуйте позже.",
        "menu": "📝 Отправьте ваш отзыв, вопрос или предложение:",
        "back": "⬅️ Назад",
        "admin_only": "Эта команда только для администратора!"
    },
    "en": {
        "start": "Hello! I'm a feedback bot. Choose language:",
        "language_selected": "Language changed to English 🇺🇸",
        "send_feedback": "Send your feedback, question or suggestion:",
        "feedback_sent": "✅ Your message has been sent to the administrator!",
        "cancel": "❌ Cancelled",
        "new_feedback": "📨 New message from user:",
        "user_info": "👤 User:",
        "reply": "📤 Reply sent to user!",
        "error": "❌ An error occurred. Please try again later.",
        "menu": "📝 Send your feedback, question or suggestion:",
        "back": "⬅️ Back",
        "admin_only": "This command is for administrators only!"
    },
    "uz": {
        "start": "Salom! Men fikr-mulohaza botiman. Tilni tanlang:",
        "language_selected": "Til o'zbek tiliga o'zgartirildi 🇺🇿",
        "send_feedback": "Fikringiz, savolingiz yoki taklifingizni yuboring:",
        "feedback_sent": "✅ Xabaringiz administratorga yuborildi!",
        "cancel": "❌ Bekor qilindi",
        "new_feedback": "📨 Foydalanuvchidan yangi xabar:",
        "user_info": "👤 Foydalanuvchi:",
        "reply": "📤 Foydalanuvchiga javob yuborildi!",
        "error": "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
        "menu": "📝 Fikringiz, savolingiz yoki taklifingizni yuboring:",
        "back": "⬅️ Orqaga",
        "admin_only": "Bu buyruq faqat administratorlar uchun!"
    }
}

# Состояния FSM
class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()
    waiting_for_reply = State()

# Хранение данных пользователей (в реальном проекте используйте БД)
user_data = {}
admin_messages = {}

# Клавиатура выбора языка
def language_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"))
    keyboard.add(InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"))
    keyboard.add(InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"))
    return keyboard.as_markup()

# Главное меню
def main_menu_keyboard(lang: str):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text=TEXTS[lang]["send_feedback"][:20] + "...", 
        callback_data="send_feedback"
    ))
    keyboard.add(InlineKeyboardButton(
        text="🌐 " + {"ru": "Язык", "en": "Language", "uz": "Til"}[lang],
        callback_data="change_language"
    ))
    return keyboard.as_markup()

# Команда /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    # По умолчанию язык - русский
    user_data[user_id] = {"lang": "ru"}
    
    await message.answer(
        TEXTS["ru"]["start"],
        reply_markup=language_keyboard()
    )

# Обработка выбора языка
@router.callback_query(F.data.startswith("lang_"))
async def process_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # Сохраняем выбранный язык
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["lang"] = lang
    
    await callback.message.edit_text(
        TEXTS[lang]["language_selected"],
        reply_markup=main_menu_keyboard(lang)
    )
    await callback.answer()

# Обработка кнопки "Изменить язык"
@router.callback_query(F.data == "change_language")
async def change_language(callback: CallbackQuery):
    await callback.message.edit_text(
        TEXTS[user_data.get(callback.from_user.id, {}).get("lang", "ru")]["start"],
        reply_markup=language_keyboard()
    )
    await callback.answer()

# Обработка отправки отзыва
@router.callback_query(F.data == "send_feedback")
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    
    await state.set_state(FeedbackStates.waiting_for_feedback)
    await callback.message.edit_text(
        TEXTS[lang]["send_feedback"],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=TEXTS[lang]["back"], callback_data="back_to_menu")
        ]])
    )
    await callback.answer()

# Кнопка "Назад"
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    
    await callback.message.edit_text(
        TEXTS[lang]["menu"],
        reply_markup=main_menu_keyboard(lang)
    )
    await callback.answer()

# Получение отзыва от пользователя
@router.message(FeedbackStates.waiting_for_feedback)
async def receive_feedback(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    
    try:
        # Отправляем сообщение администратору
        admin_text = (
            f"{TEXTS[lang]['new_feedback']}\n\n"
            f"{message.text}\n\n"
            f"{TEXTS[lang]['user_info']}\n"
            f"ID: {user_id}\n"
            f"Имя: {message.from_user.full_name}\n"
            f"Username: @{message.from_user.username if message.from_user.username else 'нет'}"
        )
        
        # Создаем клавиатуру для ответа
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="📤 Ответить",
            callback_data=f"reply_{user_id}"
        ))
        
        admin_msg = await bot.send_message(
            ADMIN_ID,
            admin_text,
            reply_markup=keyboard.as_markup()
        )
        
        # Сохраняем связь между сообщениями
        admin_messages[admin_msg.message_id] = {
            "user_id": user_id,
            "user_message_id": message.message_id
        }
        
        await message.answer(
            TEXTS[lang]["feedback_sent"],
            reply_markup=main_menu_keyboard(lang)
        )
        
    except Exception as e:
        logger.error(f"Error sending feedback: {e}")
        await message.answer(
            TEXTS[lang]["error"],
            reply_markup=main_menu_keyboard(lang)
        )
    
    await state.clear()

# Администратор нажимает "Ответить"
@router.callback_query(F.data.startswith("reply_"))
async def start_reply(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        lang = user_data.get(callback.from_user.id, {}).get("lang", "ru")
        await callback.answer(TEXTS[lang]["admin_only"], show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[1])
    
    # Сохраняем ID пользователя для ответа
    await state.update_data(reply_user_id=user_id)
    await state.set_state(FeedbackStates.waiting_for_reply)
    
    await callback.message.answer("Введите ваш ответ:")
    await callback.answer()

# Администратор отправляет ответ
@router.message(FeedbackStates.waiting_for_reply)
async def send_reply_to_user(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    
    if user_id:
        try:
            # Отправляем ответ пользователю
            lang = user_data.get(user_id, {}).get("lang", "ru")
            reply_text = f"📩 Ответ от администратора:\n\n{message.text}"
            
            await bot.send_message(user_id, reply_text)
            await message.answer("✅ Ответ отправлен пользователю!")
            
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            await message.answer("❌ Не удалось отправить ответ")
    
    await state.clear()

# Обработка текстовых сообщений (если не в состоянии)
@router.message()
async def handle_text(message: Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    
    # Если это ответ администратора на пересланное сообщение
    if message.from_user.id == ADMIN_ID and message.reply_to_message:
        original_message = message.reply_to_message
        if original_message.from_user.id == bot.id:
            # Ищем user_id в тексте сообщения
            import re
            match = re.search(r"ID: (\d+)", original_message.text)
            if match:
                user_id = int(match.group(1))
                try:
                    await bot.send_message(
                        user_id,
                        f"📩 Ответ от администратора:\n\n{message.text}"
                    )
                    await message.answer("✅ Ответ отправлен!")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    await message.answer("❌ Не удалось отправить ответ")
            return
    
    # Обычное сообщение - показываем меню
    await message.answer(
        TEXTS[lang]["menu"],
        reply_markup=main_menu_keyboard(lang)
    )

# Основная функция
async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
