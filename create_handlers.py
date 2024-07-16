import json
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
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
    TYPE,
)
from database import save_ad_to_db, load_ad_by_id
from myads_handlers import view_ad


async def create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    user_data = {"text": "", "photos": [], "username": username, "is_posted": 0}
    redis_client.set(user_id, json.dumps(user_data))
    keyboard = [
        [KeyboardButton("Long Term"), KeyboardButton("Short Term")],
        [KeyboardButton("Long Term and Short Term")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "What is the type of the rent?", reply_markup=reply_markup
    )
    return TYPE


async def handle_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["type"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text("What is the price? AED/Year")
    return PRICE


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    try:
        price = int(update.message.text)
        user_data["price"] = price
        redis_client.set(user_id, json.dumps(user_data))
        await update.message.reply_text("What is the name of the building?")
        return BUILDING
    except ValueError:
        await update.message.reply_text("Invalid price. Please enter a numeric value.")
        return PRICE


async def handle_building(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["building"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text("What is the district?")
    return DISTRICT


async def handle_district(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["district"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    keyboard = [
        [KeyboardButton("Studio"), KeyboardButton("1")],
        [KeyboardButton("2"), KeyboardButton("3")],
        [KeyboardButton("4+")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "How many rooms does your apartment have?", reply_markup=reply_markup
    )
    return ROOMS


async def handle_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["rooms"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text("What is the area of the apartment? (sqm)")
    return AREA


async def handle_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    try:
        area = int(update.message.text)
        user_data["area"] = area
        redis_client.set(user_id, json.dumps(user_data))
        await update.message.reply_text("Please send me the text for your ad.")
        return TEXT
    except ValueError:
        await update.message.reply_text("Invalid area. Please enter a numeric value.")
        return AREA


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["text"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text("Please send me the photos.")
    return PHOTOS


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    photo_file_id = update.message.photo[-1].file_id
    user_data["photos"].append(photo_file_id)
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text(
        "Photo received. You can send more photos or use /save_ad to see the ad preview before posting it."
    )
    return PHOTOS


async def save_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data_json = redis_client.get(user_id)

    if user_data_json is None:
        await update.message.reply_text("No ad data found.")
        return ConversationHandler.END

    user_data = json.loads(user_data_json)
    ad_id = save_ad_to_db(user_id, user_data)
    load_ad_by_id(ad_id)

    await update.message.reply_text(
        "Your ad has been saved.",
    )
    await view_ad(update, context)

    return ConversationHandler.END
