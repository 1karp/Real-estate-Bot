import json

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

from conversation_states import AREA, BUILDING, DISTRICT, PHOTOS, PRICE, ROOMS, TEXT
from database import load_ad_by_id, save_ad_to_db
from myads_handlers import view_ad
from settings import redis_client
from validators import validate_and_save_field


async def create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id
    username = user.username
    user_data = {
        "user_id": user_id,
        "text": "",
        "photos": [],
        "username": username,
        "is_posted": 0,
        "type": "Long Term",
    }
    redis_client.set(user_id, json.dumps(user_data))
    keyboard = [
        [KeyboardButton("Studio"), KeyboardButton("1")],
        [KeyboardButton("2"), KeyboardButton("3")],
        [KeyboardButton("4+")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.effective_message.reply_text(
        "Let's start creating your ad! 🏠\nFirst, how many rooms does your apartment have?",
        reply_markup=reply_markup,
    )
    return ROOMS


async def handle_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    success, error_message = validate_and_save_field(
        user_id, "rooms", update.effective_message.text
    )
    if success:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_rooms")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "Great! Now, what's the size of your apartment in square meters?",
            reply_markup=reply_markup,
        )
        return AREA
    else:
        await update.effective_message.reply_text(
            f"Oops! {error_message} Let's try again."
        )
        return ROOMS


async def handle_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    success, error_message = validate_and_save_field(
        user_id, "area", update.effective_message.text
    )
    if success:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_area")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "Excellent! What's the yearly rent for your apartment in AED?",
            reply_markup=reply_markup,
        )
        return PRICE
    else:
        await update.effective_message.reply_text(
            f"Oops! {error_message} Let's try again."
        )
        return AREA


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    success, error_message = validate_and_save_field(
        user_id, "price", update.effective_message.text
    )
    if success:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_price")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "Perfect! What's the name of the building your apartment is in?",
            reply_markup=reply_markup,
        )
        return BUILDING
    else:
        await update.effective_message.reply_text(
            f"Oops! {error_message} Let's try again."
        )
        return PRICE


async def handle_building(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    success, error_message = validate_and_save_field(
        user_id, "building", update.effective_message.text
    )
    if success:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_building")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "Thanks! In which district or area is your apartment located?",
            reply_markup=reply_markup,
        )
        return DISTRICT
    else:
        await update.effective_message.reply_text(
            f"Oops! {error_message} Let's try again."
        )
        return BUILDING


async def handle_district(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    success, error_message = validate_and_save_field(
        user_id, "district", update.effective_message.text
    )
    if success:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_district")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "Awesome! Now, let's add some details to make your ad stand out. 🌟\n"
            "Describe your apartment and mention any special features. "
            "What would you want to know if you were looking to rent?",
            reply_markup=reply_markup,
        )
        return TEXT
    else:
        await update.effective_message.reply_text(
            f"Oops! {error_message} Let's try again."
        )
        return DISTRICT


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    success, error_message = validate_and_save_field(
        user_id, "text", update.effective_message.text
    )
    if success:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_text")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "Great description! 📝 Now, let's add some photos to showcase your apartment. Send me up to 10 photos!",
            reply_markup=reply_markup,
        )
        return PHOTOS
    else:
        await update.effective_message.reply_text(
            f"Oops! {error_message} Let's try again."
        )
        return TEXT


async def back_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_rooms":
        return await create(update, context)
    elif query.data == "back_to_area":
        keyboard = [
            [KeyboardButton("Studio"), KeyboardButton("1")],
            [KeyboardButton("2"), KeyboardButton("3")],
            [KeyboardButton("4"), KeyboardButton("5")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await query.message.reply_text(
            "No problem, let's go back. How many rooms does your apartment have?",
            reply_markup=reply_markup,
        )
        return ROOMS
    elif query.data == "back_to_price":
        await query.message.reply_text(
            "Let's revise that. What's the size of your apartment in square meters?"
        )
        return AREA
    elif query.data == "back_to_building":
        await query.message.reply_text(
            "Sure, let's go back. What's the yearly rent for your apartment in AED?"
        )
        return PRICE
    elif query.data == "back_to_district":
        await query.message.reply_text(
            "No problem, let's revise. What's the name of the building your apartment is in?"
        )
        return BUILDING
    elif query.data == "back_to_text":
        await query.message.reply_text(
            "Alright, let's go back. In which district or area is your apartment located?"
        )
        return DISTRICT
    elif query.data == "back_to_photos":
        await query.message.reply_text(
            "Sure, let's revise your description. Please send me the text for your ad again."
        )
        return TEXT


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = json.loads(redis_client.get(user_id))
    photo_file_id = update.message.photo[-1].file_id

    photos_count = len(user_data["photos"])
    max_photos = 10
    remaining = max_photos - photos_count

    if remaining <= 0:
        await update.effective_message.reply_text(
            "Amazing! You've added the maximum of 10 photos. 📸✨\n"
            "Your ad is looking great! To review it before posting, just use the /save_ad command."
        )
    else:
        user_data["photos"].append(photo_file_id)
        redis_client.set(user_id, json.dumps(user_data))

        if remaining > 1:
            await update.effective_message.reply_text(
                f"Photo received! 📸 You can add {remaining} more photos.\n"
                f"Send another photo or use /save_ad when you're ready to preview your ad."
            )
        else:
            await update.effective_message.reply_text(
                "Photo received! 📸 You can add 1 more photo.\n"
                "Send another photo or use /save_ad when you're ready to preview your ad."
            )

    return PHOTOS


async def save_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data_json = redis_client.get(user_id)

    if user_data_json is None:
        await update.effective_message.reply_text(
            "Oops! We couldn't find your ad data. Let's start over."
        )
        return ConversationHandler.END

    user_data = json.loads(user_data_json)
    ad_id = save_ad_to_db(user_id, user_data)
    load_ad_by_id(ad_id)

    await update.effective_message.reply_text(
        "Great job! Your ad has been saved successfully. 🎉",
    )
    await view_ad(update, context)

    return ConversationHandler.END
