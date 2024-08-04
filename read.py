import requests
from bs4 import BeautifulSoup
import json
import os
from telegram import Bot
import asyncio
from telegram.constants import ParseMode
from datetime import datetime
from telegram.error import BadRequest
from games_list import games  # Importing the games list from games_list.py
import sys
from telegram.error import BadRequest
import time
import logging


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

async def send_telegram_message(game, status, srp):
    status_icon = "🔥" if status == "Hot" else "❄️" if status == "Cold" else ""
    processed_text = game.replace('-', ' ').upper()
    message = f"<b>{processed_text}</b>\nStatus : {status} {status_icon}\nSRP : {srp}%"
    sent_message = await bot.send_message(chat_id=telegram_channel_id, text=message, parse_mode=ParseMode.HTML)
    return sent_message.message_id

async def delete_telegram_message(message_id):
    try:
        await bot.delete_message(chat_id=telegram_channel_id, message_id=message_id)
    except Exception as e:
        print(f"{datetime.now()} - Failed to delete message: {e}")

async def edit_telegram_message(message_id, game, status, srp):
    status_icon = "🔥" if status == "Hot" else "❄️" if status == "Cold" else ""
    processed_text = game.replace('-', ' ').upper()
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = (f"<b>{processed_text}</b>\n"
               f"Status : {status} {status_icon}\n"
               f"SRP : {srp}%\n"
               f"Last Updated : {last_updated}")
    try:
        await bot.edit_message_text(chat_id=telegram_channel_id, message_id=message_id, text=message, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            print(f"{datetime.now()} - Message not modified for {game}.")
        else:
            print(f"{datetime.now()} - Failed to edit message: {e}")
            return False
    return True
    
async def check_and_handle_changes(game, status, srp):
    previous_status = previous_results.get(game, {}).get("status")
    previous_srp = previous_results.get(game, {}).get("SRP")
    previous_message_id = previous_results.get(game, {}).get("message_id")

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

    previous_results[game] = {
        "status": status,
        "SRP": srp,
        "last_edited": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "message_id": new_message_id
    }



async def delete_all_channel_messages():
    print(f"{datetime.now()} - Starting to delete messages from the channel")
    start_time = time.time()
    deleted_count = 0

    try:
        # Load message IDs from the JSON file
        if os.path.exists(results_file):
            with open(results_file, 'r') as file:
                data = json.load(file)
                message_ids = [info.get('message_id') for info in data.values() if info.get('message_id')]
        else:
            message_ids = []

        if not message_ids:
            print(f"{datetime.now()} - No message IDs found in {results_file}")
            return

        for message_id in message_ids:
            await delete_telegram_message(message_id)
            deleted_count += 1
            await asyncio.sleep(0.1)  # Small delay to avoid rate limits

        elapsed_time = time.time() - start_time
        print(f"Finished deleting messages. Deleted: {deleted_count}. Time taken: {elapsed_time:.2f} seconds")
        

    
    except Exception as e:
        print(f"Failed to delete messages: {e}")
        

async def delete_message(message_id):
    try:
        await bot.delete_message(chat_id=telegram_channel_id, message_id=message_id)
        return True
    except BadRequest as e:
        if "Message to delete not found" in str(e):
            return False
        elif "Message can't be deleted" in str(e):
            print(f"Couldn't delete message {message_id}: {e}")
            return False
        else:
            raise
    except Exception as e:
        print(f"Error deleting message {message_id}: {e}")
        return False
    print(f"{datetime.now()} - Starting to delete all messages from the channel")
    try:
        # Start from a high message ID and work backwards
        max_message_id = 1000000  # Adjust this number if needed
        deleted_count = 0
        
        for message_id in range(max_message_id, 0, -1):
            try:
                await bot.delete_message(chat_id=telegram_channel_id, message_id=message_id)
                deleted_count += 1
                print(f"Deleted message {message_id}")
            except BadRequest as e:
                if "Message to delete not found" in str(e):
                    # Message doesn't exist, continue to the next one
                    continue
                elif "Message can't be deleted" in str(e):
                    # Can't delete this message, continue to the next one
                    print(f"Couldn't delete message {message_id}: {e}")
                    continue
                else:
                    # Other BadRequest error, raise it
                    raise
            except Exception as e:
                print(f"Error deleting message {message_id}: {e}")
            
            # Add a small delay to avoid hitting rate limits
            await asyncio.sleep(0.1)
            
            # If we've deleted 1000 messages without finding any more, we can probably stop
            if deleted_count > 0 and message_id < max_message_id - 1000:
                break

        print(f"{datetime.now()} - Finished deleting messages. Deleted {deleted_count} messages.")
    except Exception as e:
        print(f"{datetime.now()} - Failed to delete all messages: {e}")
    print(f"{datetime.now()} - Starting to delete all messages from the channel")
    try:
        # Get the latest message in the channel
        messages = await bot.get_chat_history(chat_id=telegram_channel_id, limit=1)
        if not messages:
            print(f"{datetime.now()} - No messages found in the channel")
            return

        latest_message_id = messages[0].message_id

        # Delete messages in reverse order
        for message_id in range(latest_message_id, 0, -1):
            try:
                await bot.delete_message(chat_id=telegram_channel_id, message_id=message_id)
                print(f"Deleted message {message_id}")
            except BadRequest as e:
                if "Message to delete not found" in str(e):
                    # Message already deleted or doesn't exist, continue to the next one
                    continue
                elif "Message can't be deleted" in str(e):
                    # Can't delete this message, continue to the next one
                    print(f"Couldn't delete message {message_id}: {e}")
                    continue
                else:
                    # Other BadRequest error, raise it
                    raise
            except Exception as e:
                print(f"Error deleting message {message_id}: {e}")

        print(f"{datetime.now()} - Finished deleting all messages from the channel")
    except Exception as e:
        print(f"{datetime.now()} - Failed to delete all messages: {e}")
    print(f"{datetime.now()} - Starting to delete all messages from the channel")
    try:
        # Get the latest message in the channel
        messages = await bot.get_chat_history(chat_id=telegram_channel_id, limit=1)
        if not messages:
            print(f"{datetime.now()} - No messages found in the channel")
            return

        latest_message_id = messages[0].message_id

        # Delete messages in reverse order
        for message_id in range(latest_message_id, 0, -1):
            try:
                await bot.delete_message(chat_id=telegram_channel_id, message_id=message_id)
                print(f"Deleted message {message_id}")
            except BadRequest as e:
                if "Message to delete not found" in str(e):
                    # Message already deleted or doesn't exist, continue to the next one
                    continue
                elif "Message can't be deleted" in str(e):
                    # Can't delete this message, continue to the next one
                    print(f"Couldn't delete message {message_id}: {e}")
                    continue
                else:
                    # Other BadRequest error, raise it
                    raise
            except Exception as e:
                print(f"Error deleting message {message_id}: {e}")

        print(f"{datetime.now()} - Finished deleting all messages from the channel")
    except Exception as e:
        print(f"{datetime.now()} - Failed to delete all messages: {e}")

def delete_game_statuses_file():
    try:
        os.remove(results_file)
        print(f"{datetime.now()} - {results_file} deleted")
    except FileNotFoundError:
        print(f"{datetime.now()} - {results_file} not found")
    except Exception as e:
        print(f"{datetime.now()} - Failed to delete {results_file}: {e}")

async def perform_checks():
    print(f"{datetime.now()} - Regular checks started")
    for game in games:
        url = f"{base_url}/{game}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"{datetime.now()} - Failed to retrieve data for {game}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        snow_icon = soup.find('i', class_='snow')
        fire_icon = soup.find('i', class_='fire')

        if snow_icon:
            game_status = "Cold"
        elif fire_icon:
            game_status = "Hot"
        else:
            game_status = "Unknown"

        srp_tag = soup.find('p', class_='rtpBig')

        if srp_tag:
            srp_text = srp_tag.text
            srp_value = srp_text.split(':')[-1].strip().rstrip('%')
        else:
            srp_value = None

        await check_and_handle_changes(game, game_status, srp_value)
        await asyncio.sleep(1)

    with open(results_file, 'w') as file:
        json.dump(previous_results, file, indent=4)
    print(f"{datetime.now()} - Regular checks ended")

async def perform_cleanup():
    print(f"{datetime.now()} - Nightly cleanup started")
    await delete_all_channel_messages()
    delete_game_statuses_file()
    global previous_results
    previous_results = {}
    print(f"{datetime.now()} - Nightly cleanup ended")

async def main():
    if len(sys.argv) < 2:
        print("Please specify 'check' or 'cleanup' as an argument.")
        return

    action = sys.argv[1]

    if action == 'check':
        await perform_checks()
    elif action == 'cleanup':
        await perform_cleanup()
    else:
        print("Invalid argument. Use 'check' or 'cleanup'.")

if __name__ == "__main__":
    asyncio.run(main())