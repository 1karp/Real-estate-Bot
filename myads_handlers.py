import json
from telegram import (
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

from settings import redis_client
from database import fetch_ads_by_userid, load_ad_by_id, post_ad, edit_post_ad


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
        ]
        if ad.get("is_posted"):
            buttons.append(
                InlineKeyboardButton(
                    "Update Channel Post", callback_data=f"edit_post_ad_{ad.get('id')}"
                )
            )
        else:
            buttons.append(
                InlineKeyboardButton("Post", callback_data=f"post_ad_{ad.get('id')}")
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
    user_id = update.effective_user.id
    ads = fetch_ads_by_userid(user_id)
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
        load_ad_by_id(ad_id)
        await view_ad(update, context)


async def post_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    ad_id = query.data.split("_")[2]

    if user_data["is_posted"]:
        await query.message.reply_text("This ad has already been posted.")
        return ConversationHandler.END

    if post_ad(ad_id):
        load_ad_by_id(ad_id)
        await query.message.reply_text(
            "Ad posted successfully. Use /create to post a new ad."
        )
        return ConversationHandler.END
    else:
        await query.message.reply_text("Ad is already posted.")
        return ConversationHandler.END


async def edit_post_ad_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    ad_id = query.data.split("_")[3]

    if edit_post_ad(ad_id):
        await query.message.reply_text("Ad updated successfully.")
        return ConversationHandler.END
    else:
        await query.message.reply_text("Ad is already updated.")
        return ConversationHandler.END
