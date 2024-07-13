import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from settings import redis_client
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
