import json
from telegram import (
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from settings import redis_client
from database import fetch_ad_by_id, fetch_ads_by_username


async def get_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = update.effective_user.id
    ad_id = int(query.data.split("_")[1])
    ad = fetch_ad_by_id(ad_id)

    if ad:
        username, photos, rooms, price, type, area, house_name, district, text = ad
        user_data = {
            "ad_id": ad_id,
            "user_id": user_id,
            "username": username,
            "photos": photos,
            "rooms": rooms,
            "price": price,
            "type": type,
            "area": area,
            "house_name": house_name,
            "district": district,
            "text": text,
        }

        redis_client.set(user_id, json.dumps(user_data))

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
            media = [
                InputMediaPhoto(media=photo, caption=(ad_text if i == 0 else ""))
                for i, photo in enumerate(photos)
            ]
            await context.bot.send_media_group(
                chat_id=query.message.chat_id, media=media
            )

        button = InlineKeyboardButton("Edit", callback_data=f"edit_ad_{user_id}")
        keyboard = InlineKeyboardMarkup([[button]])
        await query.message.reply_text(
            "Preview your ad above. Click Edit to make changes.",
            reply_markup=keyboard,
        )
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
