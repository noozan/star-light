from telegram import Bot
from telegram.ext import Updater
import time

telegram_bot_token = '7320334242:AAE2wIj6HoAcm8pBmdXUCR_5ylcSLDEkbMY'
telegram_channel_id = '-1002193508333'

bot = Bot(token=telegram_bot_token)

def delete_all_messages():
    updates = bot.get_updates()
    for update in updates:
        message = update.message
        if message and message.chat.id == int(telegram_channel_id):
            try:
                bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                time.sleep(0.1)  # To avoid hitting rate limits
            except Exception as e:
                print(f"Failed to delete message {message.message_id}: {e}")

if __name__ == "__main__":
    delete_all_messages()
