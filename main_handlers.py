from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from database import save_user_to_db


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    save_user_to_db(user_id, username)

    keyboard = [[KeyboardButton("/create")], [KeyboardButton("/get_my_ads")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "👋 Welcome to Easy Rent Bot! Your friendly assistant for managing rental ads.\n\n"
        "What would you like to do today?",
        reply_markup=reply_markup,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "No worries! Your current action has been cancelled. 😊\n"
        "If you'd like to start a new ad, just tap 'Create New Ad 🏠' or use the /create command."
    )
    return ConversationHandler.END
