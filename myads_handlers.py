import json
from telegram import (
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

from settings import redis_client, CHANNEL_USERNAME
from database import fetch_ads_by_username, load_ad_by_id, update_ad


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
            f"Building: {ad.get('building')}\n"
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
        buttons = [
            InlineKeyboardButton("Edit", callback_data=f"edit_ad_{user_id}"),
            InlineKeyboardButton(
                "Update Channel Post", callback_data="update_channel_post"
            ),
        ]
        if not ad.get("is_posted"):
            buttons.append(
                InlineKeyboardButton("Post", callback_data=f"post_ad_{user_id}")
            )
        keyboard = InlineKeyboardMarkup([buttons])

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


async def post_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = json.loads(redis_client.get(user_id))

    if user_data["is_posted"]:
        await query.message.reply_text("This ad has already been posted.")
        return ConversationHandler.END

    if user_data:
        user_data["is_posted"] = 1
        redis_client.set(user_id, json.dumps(user_data))
        update_ad(user_id)
        district_hash = "_".join(user_data["district"].split())
        if int(user_data["price"]) // 10_000 * 10_000 == int(user_data["price"]):
            price_hash = int(user_data["price"])
        else:
            price_hash = (int(user_data["price"]) // 10_000 + 1) * 10_000

        text = (
            f"#{district_hash}, #under_{price_hash}\n\n"
            f"Rooms: {user_data['rooms']}\n"
            f"Price: {user_data['price']} AED/Year\n"
            f"Type: {user_data['type']}\n"
            f"Area: {user_data['area']} sqm\n"
            f"Building: {user_data['building']}\n"
            f"District: {user_data['district']}\n\n"
            f"{user_data['text']}\n\n"
            f"Contact: @{user_data['username']}"
        )
        photos = user_data["photos"].split(",")

        if photos:
            media = [
                InputMediaPhoto(media=photo, caption=(text if i == 0 else ""))
                for i, photo in enumerate(photos)
            ]
            messages = await context.bot.send_media_group(
                chat_id=CHANNEL_USERNAME, media=media
            )
            user_data["chat_message_id"] = messages[0].message_id
            load_ad_by_id(user_data.get("ad_id"), user_id)

        await query.message.reply_text(
            f"Your message has been posted. Ad ID: {user_data['id']}. Use /create to post another ad."
        )
    if user_data is None:
        await update.message.reply_text("No ad data found.")
        return ConversationHandler.END
