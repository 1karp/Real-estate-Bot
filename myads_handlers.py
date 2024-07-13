import json
from telegram import (
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from settings import redis_client
from database import fetch_ads_by_username, load_ad_by_id


async def view_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    ad = json.loads(redis_client.get(user_id))

    if ad:
        photos = ad.get("photos").split(",")
        ad_text = (
            f"{ad.get('text')}\n\n"
            f"Rooms: {ad.get('rooms')}\n"
            f"Price: {ad.get('price')} AED/year\n"
            f"Rent type: {ad.get('type')}\n"
            f"Area: {ad.get('area')} sqm\n"
            f"House Name: {ad.get('house_name')}\n"
            f"District: {ad.get('district')}\n\n"
            f"Contact: @{ad.get('username')}"
        )

        if photos:
            media = [
                InputMediaPhoto(media=photo, caption=(ad_text if i == 0 else ""))
                for i, photo in enumerate(photos)
            ]
            await context.bot.send_media_group(
                chat_id=update.effective_chat.id, media=media
            )

        button = InlineKeyboardButton("Edit", callback_data=f"edit_ad_{user_id}")
        keyboard = InlineKeyboardMarkup([[button]])

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Preview your ad above. Click Edit to make changes.",
            reply_markup=keyboard,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No ad found. To create a new ad, use /create.",
        )


async def get_my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    ads = fetch_ads_by_username(username)
    if ads:
        buttons = [
            [InlineKeyboardButton(f"Ad ID: {ad[0]}", callback_data=f"view_ad_{ad[0]}")]
            for ad in ads
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            "Here are your ads. Click on an ID to view the ad details:",
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            "No ads found for you. To create a new ad, use /create."
        )


async def view_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("view_ad_"):
        ad_id = data.split("_")[2]
        user_id = update.effective_user.id
        load_ad_by_id(ad_id, user_id)
        await view_ad(update, context)
