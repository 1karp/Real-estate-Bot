import json
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from settings import redis_client
from conversation_states import (
    AREA,
    DISTRICT,
    BUILDING,
    PHOTOS,
    PRICE,
    ROOMS,
    TEXT,
)
from database import save_ad_to_db, load_ad_by_id
from myads_handlers import view_ad


async def create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id
    username = user.username
    user_data = {
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
        "How many rooms does your apartment have?", reply_markup=reply_markup
    )
    return ROOMS


async def handle_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["rooms"] = update.effective_message.text
    redis_client.set(user_id, json.dumps(user_data))
    keyboard = [[InlineKeyboardButton("Back", callback_data="back_to_rooms")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "What is the area of the apartment? (sqm)", reply_markup=reply_markup
    )
    return AREA


async def handle_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = json.loads(redis_client.get(user_id))
    try:
        area = int(update.effective_message.text)
        user_data["area"] = area
        redis_client.set(user_id, json.dumps(user_data))
        keyboard = [[InlineKeyboardButton("Back", callback_data="back_to_area")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "What is the price? AED/Year", reply_markup=reply_markup
        )
        return PRICE
    except ValueError:
        await update.effective_message.reply_text(
            "Invalid area. Please enter a numeric value."
        )
        return AREA


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = json.loads(redis_client.get(user_id))
    try:
        price = int(update.effective_message.text)
        user_data["price"] = price
        redis_client.set(user_id, json.dumps(user_data))
        keyboard = [[InlineKeyboardButton("Back", callback_data="back_to_price")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "What is the name of the building?", reply_markup=reply_markup
        )
        return BUILDING
    except ValueError:
        await update.effective_message.reply_text(
            "Invalid price. Please enter a numeric value."
        )
        return PRICE


async def handle_building(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["building"] = update.effective_message.text
    redis_client.set(user_id, json.dumps(user_data))
    keyboard = [[InlineKeyboardButton("Back", callback_data="back_to_building")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "What is the district?", reply_markup=reply_markup
    )
    return DISTRICT


async def handle_district(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["district"] = update.effective_message.text
    redis_client.set(user_id, json.dumps(user_data))
    keyboard = [[InlineKeyboardButton("Back", callback_data="back_to_district")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "Please send me the text for your ad.", reply_markup=reply_markup
    )
    return TEXT


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["text"] = update.effective_message.text
    redis_client.set(user_id, json.dumps(user_data))
    keyboard = [[InlineKeyboardButton("Back", callback_data="back_to_text")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "Please send me the photos.", reply_markup=reply_markup
    )
    return PHOTOS


async def back_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_rooms":
        return await create(update, context)
    elif query.data == "back_to_area":
        keyboard = [
            [KeyboardButton("Studio"), KeyboardButton("1")],
            [KeyboardButton("2"), KeyboardButton("3")],
            [KeyboardButton("4+")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await query.message.reply_text(
            "How many rooms does your apartment have?", reply_markup=reply_markup
        )
        return ROOMS
    elif query.data == "back_to_price":
        await query.message.reply_text("What is the area of the apartment? (sqm)")
        return AREA
    elif query.data == "back_to_building":
        await query.message.reply_text("What is the price? AED/Year")
        return PRICE
    elif query.data == "back_to_district":
        await query.message.reply_text("What is the name of the building?")
        return BUILDING
    elif query.data == "back_to_text":
        await query.message.reply_text("What is the district?")
        return DISTRICT
    elif query.data == "back_to_photos":
        await query.message.reply_text("Please send me the text for your ad.")
        return TEXT


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data = json.loads(redis_client.get(user_id))
    photo_file_id = update.message.photo[-1].file_id

    if len(user_data["photos"]) >= 10:
        await update.effective_message.reply_text(
            "You've already added the maximum of 10 photos. "
            "Please use /save_ad to see the ad preview before posting it."
        )
    else:
        user_data["photos"].append(photo_file_id)
        redis_client.set(user_id, json.dumps(user_data))

        photos_count = len(user_data["photos"])
        remaining = 10 - photos_count

        if remaining > 0:
            await update.effective_message.reply_text(
                f"Photo received. You can send {remaining} more photo{'s' if remaining > 1 else ''} "
                f"or use /save_ad to see the ad preview before posting it."
            )
        else:
            await update.effective_message.reply_text(
                "You've added the maximum of 10 photos. "
                "Please use /save_ad to see the ad preview before posting it."
            )

    return PHOTOS


async def save_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data_json = redis_client.get(user_id)

    if user_data_json is None:
        await update.effective_message.reply_text("No ad data found.")
        return ConversationHandler.END

    user_data = json.loads(user_data_json)
    ad_id = save_ad_to_db(user_id, user_data)
    load_ad_by_id(ad_id)

    await update.effective_message.reply_text(
        "Your ad has been saved.",
    )
    await view_ad(update, context)

    return ConversationHandler.END
