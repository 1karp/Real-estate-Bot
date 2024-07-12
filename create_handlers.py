import json
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from conversation_states import (
    AREA,
    DISTRICT,
    HOUSE_NAME,
    PHOTOS,
    PRICE,
    ROOMS,
    TEXT,
    TYPE,
    PREVIEW,
    EDIT,
    EDIT_VALUE,
)
from database import save_ad_to_db
from settings import redis_client, CHANNEL_USERNAME


# Define the start command handler function
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("/create")], [KeyboardButton("/get_ad")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "Welcome to Easy rent Bot! Please choose an option:", reply_markup=reply_markup
    )


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("You can start over with /create.")
    return ConversationHandler.END


# Define the create command handler function
async def create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    user_data = {"text": "", "photos": [], "username": username}
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


# Define a function to handle type
async def handle_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["type"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text("What is the price? AED/Year")
    return PRICE


# Define a function to handle price
async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    try:
        price = int(update.message.text)
        user_data["price"] = price
        redis_client.set(user_id, json.dumps(user_data))
        await update.message.reply_text("What is the name of the house?")
        return HOUSE_NAME
    except ValueError:
        await update.message.reply_text("Invalid price. Please enter a numeric value.")
        return PRICE


# Define a function to handle house name
async def handle_house_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["house_name"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text("What is the district?")
    return DISTRICT


# Define a function to handle district
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


# Define a function to handle number of rooms
async def handle_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["rooms"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text("What is the area of the apartment? (sqm)")
    return AREA


# Define a function to handle area
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


# Define a function to handle created text
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    user_data["text"] = update.message.text
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text("Please send me the photos.")
    return PHOTOS


# Define a function to handle created photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    photo_file_id = update.message.photo[-1].file_id
    user_data["photos"].append(photo_file_id)
    redis_client.set(user_id, json.dumps(user_data))
    await update.message.reply_text(
        "Photo received. You can send more photos or use /preview to see the ad preview."
    )
    return PHOTOS


# Define the preview command handler function
async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    if user_data:
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
            f"House Name: {user_data['house_name']}\n"
            f"District: {user_data['district']}\n\n"
            f"{user_data['text']}\n\n"
            f"Contact: @{user_data['username']}"
        )
        photos = user_data["photos"]

        media = [
            InputMediaPhoto(media=photo, caption=(text if i == 0 else ""))
            for i, photo in enumerate(photos)
        ]

        confirm_button = InlineKeyboardButton("Confirm", callback_data="confirm")
        edit_button = InlineKeyboardButton("Edit", callback_data="edit")
        keyboard = InlineKeyboardMarkup([[confirm_button, edit_button]])

        await context.bot.send_media_group(chat_id=update.message.chat_id, media=media)
        await update.message.reply_text(
            "Preview your ad above. Click Confirm to post or Edit to make changes.",
            reply_markup=keyboard,
        )

        return PREVIEW


# Define the edit handler function
async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    if user_data:
        keyboard = [
            [KeyboardButton("Type"), KeyboardButton("Price")],
            [KeyboardButton("House Name"), KeyboardButton("District")],
            [KeyboardButton("Rooms"), KeyboardButton("Area")],
            [KeyboardButton("Text"), KeyboardButton("Photos")],
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )
        await query.message.reply_text(
            "Which field would you like to edit?", reply_markup=reply_markup
        )
        return EDIT


# Define the confirmation handler function
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    if user_data:
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
            f"House Name: {user_data['house_name']}\n"
            f"District: {user_data['district']}\n\n"
            f"{user_data['text']}\n\n"
            f"Contact: @{user_data['username']}"
        )
        photos = user_data["photos"]

        ad_id = save_ad_to_db(user_id, user_data)

        if photos:
            media = [
                InputMediaPhoto(media=photo, caption=(text if i == 0 else ""))
                for i, photo in enumerate(photos)
            ]
            await context.bot.send_media_group(chat_id=CHANNEL_USERNAME, media=media)

        redis_client.delete(user_id)
        await query.message.reply_text(
            f"Your message has been posted. Ad ID: {ad_id}. Use /create to post another ad."
        )
        return ConversationHandler.END


# Define a function to handle the field to be edited
async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    field = update.message.text.lower().replace(" ", "_")
    if field in user_data:
        user_data["edit_field"] = field
        redis_client.set(user_id, json.dumps(user_data))
        await update.message.reply_text(f"Please enter the new value for {field}:")
        return EDIT_VALUE
    else:
        await update.message.reply_text("Invalid field. Please choose a valid field.")
        return EDIT


# Define a function to handle the updated field value
async def update_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = json.loads(redis_client.get(user_id))
    field = user_data.get("edit_field")
    if field:
        user_data[field] = update.message.text
        del user_data["edit_field"]
        redis_client.set(user_id, json.dumps(user_data))
        await update.message.reply_text(f"{field} updated. Returning to preview...")
        return await preview(update, context)
    else:
        await update.message.reply_text("Error updating field. Please try again.")
        return EDIT
