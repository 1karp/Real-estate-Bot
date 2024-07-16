from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from conversation_states import CHOOSING, TYPING_REPLY
from database import update_ad
from myads_handlers import view_ad
from validators import EDIT_FIELDS, validate_and_save_field


async def edit_ad_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    buttons = [
        [InlineKeyboardButton(field.capitalize(), callback_data=f"edit_{field}")]
        for field in EDIT_FIELDS
    ]
    buttons.append([InlineKeyboardButton("Save", callback_data="save")])

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

    success, error_message = validate_and_save_field(user_id, field, new_value)

    if success:
        buttons = [
            [InlineKeyboardButton(f.capitalize(), callback_data=f"edit_{f}")]
            for f in EDIT_FIELDS
        ]
        buttons.append([InlineKeyboardButton("Save and exit", callback_data="save")])

        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            f"{field.capitalize()} updated. What else would you like to edit?",
            reply_markup=reply_markup,
        )
        return CHOOSING
    else:
        await update.message.reply_text(error_message)
        return TYPING_REPLY


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
