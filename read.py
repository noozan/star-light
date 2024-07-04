import requests
from bs4 import BeautifulSoup
import json
import os
import asyncio
from telegram import Bot, ParseMode
from telegram.error import BadRequest
from datetime import datetime
from games_list import games  # Importing the games list from games_list.py


# Base URL
base_url = 'https://slotcatalog.com/en/slots'

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

# Function to send a message to the Telegram channel
async def send_telegram_message(game, status, srp):
    status_icon = "🔥" if status == "Hot" else "❄️" if status == "Cold" else ""
    processed_text = game.replace('-', ' ').upper()
    message = f"<b>{processed_text}</b>\nStatus : {status} {status_icon}\nSRP : {srp}%"
    sent_message = await bot.send_message(chat_id=telegram_channel_id, text=message, parse_mode=ParseMode.HTML)
    return sent_message.message_id

# Function to delete a message from the Telegram channel
async def delete_telegram_message(message_id):
    try:
        await bot.delete_message(chat_id=telegram_channel_id, message_id=message_id)
    except Exception as e:
        print(f"{datetime.now()} - Failed to delete message: {e}")

# Function to edit a message in the Telegram channel
async def edit_telegram_message(message_id, game, status, srp):
    status_icon = "🔥" if status == "Hot" else "❄️" if status == "Cold" else ""
    processed_text = game.replace('-', ' ').upper()
    message = f"<b>{processed_text}</b>\nStatus : {status} {status_icon}\nSRP : {srp}%"
    try:
        await bot.edit_message_text(chat_id=telegram_channel_id, message_id=message_id, text=message, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            print(f"{datetime.now()} - Message not modified for {game}.")
        else:
            print(f"{datetime.now()} - Failed to edit message: {e}")
            return False
    return True

# Function to check and handle changes
async def check_and_handle_changes(game, status, srp):
    previous_status = previous_results.get(game, {}).get("status")
    previous_srp = previous_results.get(game, {}).get("SRP")
    previous_message_id = previous_results.get(game, {}).get("message_id")

    # Check conditions for handling changes
    if status != previous_status:
        if previous_message_id:
            await delete_telegram_message(previous_message_id)
        new_message_id = await send_telegram_message(game, status, srp)
    elif status == "Hot" and srp and previous_srp and float(srp) > float(previous_srp):
        if previous_message_id:
            await delete_telegram_message(previous_message_id)
        new_message_id = await send_telegram_message(game, status, srp)
    elif status == "Hot" and srp and previous_srp and float(srp) < float(previous_srp):
        if previous_message_id:
            updated = await edit_telegram_message(previous_message_id, game, status, srp)
            if not updated:
                new_message_id = await send_telegram_message(game, status, srp)
            else:
                new_message_id = previous_message_id
    elif status == "Cold" and srp and previous_srp and float(srp) != float(previous_srp):
        if previous_message_id:
            updated = await edit_telegram_message(previous_message_id, game, status, srp)
            if not updated:
                new_message_id = await send_telegram_message(game, status, srp)
            else:
                new_message_id = previous_message_id
    else:
        new_message_id = previous_message_id

    # Update previous_results with the latest data including the message_id
    previous_results[game] = {
        "status": status,
        "SRP": srp,
        "last_edited": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "message_id": new_message_id
    }

# Main function to run the scraping and checking
async def main():
    print(f"{datetime.now()} - Script started")
    # Loop through each game identifier
    for game in games:
        # Construct the full URL for each game
        url = f"{base_url}/{game}"

        # Fetch the content from the URL
        response = requests.get(url)

        if response.status_code != 200:
            print(f"{datetime.now()} - Failed to retrieve data for {game}")
            continue

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for the presence of <i> tag with class 'snow' or 'fire'
        snow_icon = soup.find('i', class_='snow')
        fire_icon = soup.find('i', class_='fire')

        # Determine the status of the game
        if snow_icon:
            game_status = "Cold"
        elif fire_icon:
            game_status = "Hot"
        else:
            game_status = "Unknown"

        # Find the <p> tag with class 'rtpBig' for SRP percentage
        srp_tag = soup.find('p', class_='rtpBig')

        # Extract the SRP percentage
        if srp_tag:
            srp_text = srp_tag.text
            srp_value = srp_text.split(':')[-1].strip()
            # Remove '%' at the end of srp_value
            srp_value = srp_value.rstrip('%')
        else:
            srp_value = None

        # Check and handle changes
        await check_and_handle_changes(game, game_status, srp_value)

        # Wait for 10 seconds before processing the next game
        await asyncio.sleep(1)

    # Save the updated previous_results to the file
    with open(results_file, 'w') as file:
        json.dump(previous_results, file, indent=4)
    print(f"{datetime.now()} - Script ended")

# Run the main function
asyncio.run(main())