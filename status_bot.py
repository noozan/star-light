import json
import os
from telegram import Bot, Update
from telegram.ext import CommandHandler, Updater
from telegram.constants import ParseMode

# File to save previous results
results_file = 'game_statuses.json'

# Telegram bot token and channel ID
telegram_bot_token = '7320334242:AAE2wIj6HoAcm8pBmdXUCR_5ylcSLDEkbMY'
telegram_channel_id = '-1002193508333'

# Initialize the Telegram bot
bot = Bot(token=telegram_bot_token)

# Load previous results if the file exists
if os.path.exists(results_file):
    with open(results_file, 'r') as file:
        previous_results = json.load(file)
else:
    previous_results = {}

# Function to handle the /status command
def status(update: Update, context):
    status_message = ""
    for game, data in previous_results.items():
        game_name = game.replace('-', ' ').upper()
        status = data.get("status")
        srp = data.get("SRP")
        status_icon = "🔥" if status == "Hot" else "❄️" if status == "Cold" else ""
        status_message += f"<b>{game_name}</b>\nStatus : {status} {status_icon}\nSRP : {srp}%\n\n"
    update.message.reply_text(status_message, parse_mode=ParseMode.HTML)

# Setup the Updater and Dispatcher for handling commands
updater = Updater(token=telegram_bot_token, use_context=True)
dispatcher = updater.dispatcher

# Add the /status command handler
status_handler = CommandHandler('status', status)
dispatcher.add_handler(status_handler)

# Start the bot
updater.start_polling()
updater.idle()
