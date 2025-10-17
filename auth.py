from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from db import search_employees_by_name, link_telegram_id, get_employee_by_id
from location import request_location
from loader import dp
from aiogram.dispatcher.filters import Text


class AuthStates(StatesGroup):
    waiting_for_name = State()

def register(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "authorize")
    async def authorize_handler(callback_query: types.CallbackQuery):
        await callback_query.message.answer("Введите часть вашего имени для поиска:")
        await AuthStates.waiting_for_name.set()

    @dp.message_handler(state=AuthStates.waiting_for_name)
    async def search_employee(message: types.Message, state: FSMContext):
        matches = search_employees_by_name(message.text)
        if not matches:
            await message.answer("Сотрудник не найден. Попробуйте снова.")
            return


        keyboard = types.InlineKeyboardMarkup()
        for emp_id, full_name in matches:
            keyboard.add(types.InlineKeyboardButton(full_name, callback_data=f"select_{emp_id}"))
        await message.answer("Выберите себя из списка:", reply_markup=keyboard)

@dp.callback_query_handler(Text(startswith="select_"))
async def confirm_selection(callback: types.CallbackQuery):
    emp_id = callback.data.replace("select_", "")
    user_id = callback.from_user.id

    link_telegram_id(emp_id, user_id)
    employee = get_employee_by_id(emp_id)

    if not employee:
        await callback.message.answer("⚠️ Ошибка: сотрудник не найден в базе.")
        return

    full_name = employee[3]  # если full_name — 4-й столбец

    await callback.message.edit_reply_markup()
    await callback.message.answer(f"✅ Вы успешно авторизованы как {full_name}.")

    # ⬇️ Сразу предлагаем отправить геолокацию
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton(text="📍 Отправить геолокацию", request_location=True))

    await callback.message.answer("Пожалуйста, отправьте свою геолокацию для отметки входа:", reply_markup=keyboard)
