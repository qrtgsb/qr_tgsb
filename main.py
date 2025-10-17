from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN
import start
import auth
import location
from db import init_db
import admin
import location_handler
import admin_panel

print("✅ Бот запускается на Render...")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

init_db()

start.register(dp)
auth.register(dp)
location_handler.register(dp)
admin_panel.register(dp)

if __name__ == "__main__":
    try:
        print("🚀 Бот начинает слушать Telegram...")
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
