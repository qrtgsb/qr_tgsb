from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from states import LocationStates
from db import get_employee_by_telegram_id
from admin import is_admin  # ← проверка по списку админов
import time

user_timestamps = {}

def register(dp: Dispatcher):
    @dp.message_handler(commands=['start'])
    async def start_handler(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        user_timestamps[user_id] = time.time()

        # ✅ Если это админ — не запускаем обычную авторизацию
        if is_admin(user_id):
            await message.answer("👋 Привет, админ. Используй /admin для доступа к панели.")
            return

        # ✅ Обычный сотрудник — проверяем в базе
        employee = get_employee_by_telegram_id(user_id)

        if employee:
            full_name = employee[1]
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button = KeyboardButton("📍 Отправить геолокацию", request_location=True)
            keyboard.add(button)
            await LocationStates.waiting_for_location.set()
            await message.answer(
                f"Здравствуйте, {full_name}! Вы успешно авторизованы. Отправьте геолокацию для отметки входа:",
                reply_markup=keyboard
            )
        else:
            await message.answer("Введите ваше имя или фамилию для поиска:")
            await LocationStates.waiting_for_employee_search.set()
