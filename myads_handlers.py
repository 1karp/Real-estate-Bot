import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import ContextTypes, ConversationHandler

from database import (
    edit_post_ad,
    get_ads_by_userid,
    load_ad_by_id,
    post_ad,
)
from settings import redis_client


async def view_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    ad = json.loads(redis_client.get(user_id))

    if ad:
        photos = ad.get("photos").split(",")
        ad_text = (
            f"Rooms: {ad.get('rooms')}\n"
            f"Price: {ad.get('price')} AED/year\n"
            f"Rent type: {ad.get('type')}\n"
            f"Area: {ad.get('area')} sqm\n"
            f"Building: {ad.get('building')}\n"
            f"District: {ad.get('district')}\n\n"
            f"{ad.get('text')}\n\n"
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
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_ad_{user_id}"),
        ]
        if ad.get("is_posted"):
            buttons.append(
                InlineKeyboardButton(
                    "🔄 Update Channel Post",
                    callback_data=f"edit_post_ad_{ad.get('id')}",
                )
            )
        else:
            buttons.append(
                InlineKeyboardButton("📢 Post", callback_data=f"post_ad_{ad.get('id')}")
            )
        keyboard = InlineKeyboardMarkup([buttons])

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Here's a preview of your ad. 👆 Click 'Edit' if you'd like to make any changes.",
            reply_markup=keyboard,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Oops! We couldn't find any ads for you. 😕 To create a new ad, just use the /create command.",
        )


async def get_my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    ads = get_ads_by_userid(user_id)
    if ads:
        buttons = [
            [InlineKeyboardButton(f"Ad #{ad}", callback_data=f"view_ad_{ad}")]
            for ad in ads
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            "Here's a list of your ads. 📋 Tap on an ad number to view its details:",
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            "Looks like you haven't created any ads yet. 🤔 Ready to make one? Just use the /create command!"
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
        await query.message.reply_text("This ad has already been posted. 😊")
        return ConversationHandler.END

    if post_ad(ad_id):
        load_ad_by_id(ad_id)
        await query.message.reply_text(
            "Great news! Your ad has been posted successfully. 🎉\n"
            "Ready to create another? Just use the /create command."
        )
        return ConversationHandler.END
    else:
        await query.message.reply_text("It looks like this ad is already posted. 🤔")
        return ConversationHandler.END


async def edit_post_ad_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    ad_id = query.data.split("_")[3]

    if edit_post_ad(ad_id):
        await query.message.reply_text("Your ad has been updated successfully! 🎉")
        return ConversationHandler.END
    else:
        await query.message.reply_text("It seems your ad is already up to date. 👍")
        return ConversationHandler.END
