import asyncio
from aiogram import Bot
import logging

# Токен пингера (второй бот)
PINGER_TOKEN = "8264845816:AAFgKIEbLfJ017pupVPxxCi9JqZ70wlR3jw"  # ← замени на токен

# ID основного бота или чата
TARGET_CHAT_ID = 6633348914  # ← замени на chat_id

bot = Bot(token=PINGER_TOKEN)

async def send_ping():
    while True:
        try:
            await bot.send_message(TARGET_CHAT_ID, "/ping")
            logging.info("✅ Ping sent")
        except Exception as e:
            logging.error(f"❌ Error sending ping: {e}")
        await asyncio.sleep(300)  # каждые 5 минут

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(send_ping())
