import os
from dotenv import load_dotenv
from telegram import (
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from database import fetch_ad_by_id, fetch_ads_by_username

# Load environment variables
load_dotenv()
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")


# Define the get_ad command handler function
async def get_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    ad_id = int(query.data.split("_")[1])
    ad = fetch_ad_by_id(ad_id)
    if ad:
        username, photos, rooms, price, type, area, house_name, district, text = ad
        ad_text = (
            f"{text}\n\n"
            f"Rooms: {rooms}\n"
            f"Price: {price} AED/year\n"
            f"Rent type: {type}\n"
            f"Area: {area} sqm\n"
            f"House Name: {house_name}\n"
            f"District: {district}\n\n"
            f"Contact: @{username}"
        )
        if photos:
            # Create a list of InputMediaPhoto objects
            media = [
                InputMediaPhoto(media=photo, caption=(ad_text if i == 0 else ""))
                for i, photo in enumerate(photos)
            ]
            # Send the ad photos as a media group with the text as caption of the first photo
            await query.message.reply_media_group(media=media)
    else:
        await query.message.reply_text("Ad not found.")


async def get_my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    ads = fetch_ads_by_username(username)
    if ads:
        buttons = [
            [InlineKeyboardButton(f"Ad ID: {ad[0]}", callback_data=f"ad_{ad[0]}")]
            for ad in ads
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            "Here are your ads. Click on an ID to view the ad details:",
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text("No ads found for you.")
