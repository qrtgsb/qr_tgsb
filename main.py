from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.executor import start_webhook
from config import BOT_TOKEN

import start
import auth
import location
from db import init_db
import admin
import location_handler
import admin_panel

# 🌐 Webhook настройки
WEBHOOK_HOST = "https://qr-tgsb.onrender.com"  # ← замени на свой Render-домен
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 10000

# ✅ Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# 🔧 Инициализация базы данных
init_db()

# 🔧 Регистрация хендлеров
start.register(dp)
auth.register(dp)
location_handler.register(dp)
admin_panel.register(dp)

# 🚀 При старте
async def on_startup(dp):
    print(f"📡 Установка webhook на {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook установлен")

# 🛑 При завершении
async def on_shutdown(dp):
    print("❌ Отключение вебхука...")
    await bot.delete_webhook()

# 🧠 Запуск
if __name__ == "__main__":
    print("🚀 Бот запускается через Webhook...")
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
