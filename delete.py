import asyncio
from telegram import Bot
from telegram.error import TelegramError
import os

# Telegram bot token and channel ID
telegram_bot_token = '7320334242:AAE2wIj6HoAcm8pBmdXUCR_5ylcSLDEkbMY'
telegram_channel_id = '-1002193508333'

# Path to the file to be deleted
file_path = '/var/star-light/game_statuses.json'

bot = Bot(token=telegram_bot_token)

async def delete_all_messages():
    updates = await bot.get_updates()
    for update in updates:
        message = update.message
        if message and message.chat.id == int(telegram_channel_id):
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                await asyncio.sleep(0.1)  # To avoid hitting rate limits
            except TelegramError as e:
                print(f"Failed to delete message {message.message_id}: {e}")

def delete_file():
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"File {file_path} deleted successfully.")
        except Exception as e:
            print(f"Failed to delete file {file_path}: {e}")
    else:
        print(f"File {file_path} does not exist.")

async def main():
    await delete_all_messages()
    delete_file()

if __name__ == "__main__":
    asyncio.run(main())
