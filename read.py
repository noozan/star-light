import requests
from bs4 import BeautifulSoup
import json
import os
from telegram import Bot
import asyncio
from telegram.constants import ParseMode
from datetime import datetime

# List of game identifiers
games = [
    "Gates-of-Olympus",
    "Gates-of-Olympus-1000",
    "Starlight-Princess-1000",
    "Starlight-Princess",
    "Sugar-Rush-1000",
    "Sugar-Rush",
    "Fire-Portals",
    "Wanted-Dead-or-a-Wild",
    "Book-of-Dead",
    "Sweet-Bonanza",
    "Big-Bass-Splash",
    "Big-Bass-Bonanza"
]

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

# Function to send message to Telegram channel
async def send_telegram_message(game, status, srp):
    if status == "Hot":
        status_icon = "🔥"
    elif status == "Cold":
        status_icon = "❄️"
    else:
        status_icon = ""
    
    processed_text = game.replace('-', ' ').upper()

    message = f"<b>{processed_text}</b>\nStatus : {status} {status_icon}\nSRP : {srp}%"
    sent_message = await bot.send_message(chat_id=telegram_channel_id, text=message, parse_mode=ParseMode.HTML)
    return sent_message.message_id

# Function to delete message from Telegram channel
async def delete_telegram_message(game):
    if game in previous_results and 'message_id' in previous_results[game]:
        message_id = previous_results[game]['message_id']
        try:
            await bot.delete_message(chat_id=telegram_channel_id, message_id=message_id)
            print(f"Deleted previous message for {game}")
        except error.BadRequest as e:
            if e.message == 'Message to delete not found':
                print(f"Message to delete not found for {game}")
            else:
                print(f"Error deleting message for {game}: {e}")
        except error.TelegramError as e:
            print(f"Telegram error deleting message for {game}: {e}")

# Function to check and handle changes
async def check_and_handle_changes(game, status, srp):
    previous_status = previous_results.get(game, {}).get("status")
    previous_srp = previous_results.get(game, {}).get("SRP")
    previous_message_id = previous_results.get(game, {}).get("message_id")

    # Check for changes in status or significant SRP increase when status is Hot
    if status != previous_status or (status == "Hot" and srp and previous_srp and float(srp) > float(previous_srp)):
        print(f"Handling changes for {game}")

        # Delete previous message if exists
        await delete_telegram_message(game)

        # Send new message
        new_message_id = await send_telegram_message(game, status, srp)

        # Update previous_results with the latest data including the message_id
        previous_results[game] = {
            "status": status,
            "SRP": srp,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "message_id": new_message_id
        }
    # Only print messages when there are actual changes
    elif status == previous_status and (status != "Hot" or not (srp and previous_srp and float(srp) > float(previous_srp))):
        pass  # Skip printing "no changes" messages

# Main function to run the scraping and checking
async def main():
    start_time = datetime.now()
    print(f"Script started at: {start_time}")

    # Loop through each game identifier
    for game in games:
        # Construct the full URL for each game
        url = f"{base_url}/{game}"

        # Fetch the content from the URL
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to retrieve data for {game}")
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

        # Wait for a short interval before processing the next game
        await asyncio.sleep(1)  # Adjust this interval as needed

    # Save the updated previous_results to the file
    with open(results_file, 'w') as file:
        json.dump(previous_results, file, indent=4)

    end_time = datetime.now()
    print(f"Script finished at: {end_time}")
    print(f"Total execution time: {end_time - start_time}")

# Run the main function
asyncio.run(main())