import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler

from settings import redis_client, CHANNEL_USERNAME
from database import update_ad
from myads_handlers import view_ad
from conversation_states import CHOOSING, TYPING_REPLY, EDIT_FIELDS


async def edit_ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    buttons = [
        [InlineKeyboardButton(field.capitalize(), callback_data=f"edit_{field}")]
        for field in EDIT_FIELDS
    ]
    buttons.append([InlineKeyboardButton("Done", callback_data="done")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(
        "What would you like to edit?", reply_markup=reply_markup
    )
    return CHOOSING


async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    field = query.data.split("_")[1]

    context.user_data["edit_field"] = field
    await query.edit_message_text(f"Please enter the new value for {field}:")
    return TYPING_REPLY


async def save_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    field = context.user_data["edit_field"]
    new_value = update.message.text

    ad = json.loads(redis_client.get(user_id))
    ad[field] = new_value
    redis_client.set(user_id, json.dumps(ad))

    buttons = [
        [InlineKeyboardButton(f.capitalize(), callback_data=f"edit_{f}")]
        for f in EDIT_FIELDS
    ]
    buttons.append([InlineKeyboardButton("Done", callback_data="done")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        f"{field.capitalize()} updated. What else would you like to edit?",
        reply_markup=reply_markup,
    )
    return CHOOSING


async def finish_editing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    update_ad(user_id)

    await query.edit_message_text("Editing completed. Here's your updated ad:")
    await view_ad(update, context)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Editing cancelled.")
    return ConversationHandler.END


async def edit_ad_in_channel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = json.loads(redis_client.get(user_id))

    if not user_data:
        await query.message.reply_text("No ad data found.")
        return

    district_hash = "_".join(user_data["district"].split())
    if int(user_data["price"]) // 10_000 * 10_000 == int(user_data["price"]):
        price_hash = int(user_data["price"])
    else:
        price_hash = (int(user_data["price"]) // 10_000 + 1) * 10_000

    new_text = (
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
        new_media = InputMediaPhoto(media=photos[0], caption=new_text)
        try:
            await context.bot.edit_message_media(
                chat_id=CHANNEL_USERNAME,
                message_id=user_data["channel_message_id"],
                media=new_media,
            )
        except Exception as e:
            await query.message.reply_text(f"Failed to edit the message: {str(e)}")
            return

        for i, photo in enumerate(photos[1:], start=1):
            new_media = InputMediaPhoto(media=photo)
            try:
                await context.bot.edit_message_media(
                    chat_id=CHANNEL_USERNAME,
                    message_id=user_data["channel_message_id"] + i,
                    media=new_media,
                )
            except Exception as e:
                await query.message.reply_text(f"Failed to edit photo {i+1}: {str(e)}")
    else:
        try:
            await context.bot.edit_message_text(
                chat_id=CHANNEL_USERNAME,
                message_id=user_data["channel_message_id"],
                text=new_text,
            )
        except Exception as e:
            await query.message.reply_text(f"Failed to edit the message: {str(e)}")
            return

    await query.message.reply_text(
        "Your ad has been successfully updated in the channel."
    )
