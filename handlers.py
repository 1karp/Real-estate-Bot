import logging
import os

from dotenv import load_dotenv
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
from database import fetch_ad_by_id, save_ad_to_db

# Load environment variables
load_dotenv()
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

# Temporary storage for user data, redis in future
user_data = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


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
    user_data[user_id] = {"text": "", "photos": [], "username": username}
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
    user_data[user_id]["type"] = update.message.text
    await update.message.reply_text("What is the price? AED/Year")
    return PRICE


# Define a function to handle price
async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    try:
        price = float(update.message.text)
        user_data[user_id]["price"] = price
        await update.message.reply_text("What is the name of the house?")
        return HOUSE_NAME
    except ValueError:
        await update.message.reply_text("Invalid price. Please enter a numeric value.")
        return PRICE


# Define a function to handle house name
async def handle_house_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["house_name"] = update.message.text
    await update.message.reply_text("What is the district?")
    return DISTRICT


# Define a function to handle district
async def handle_district(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["district"] = update.message.text
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
    user_data[user_id]["rooms"] = update.message.text
    await update.message.reply_text("What is the area of the apartment? (sqm)")
    return AREA


# Define a function to handle area
async def handle_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    try:
        area = float(update.message.text)
        user_data[user_id]["area"] = area
        await update.message.reply_text("Please send me the text for your ad.")
        return TEXT
    except ValueError:
        await update.message.reply_text("Invalid area. Please enter a numeric value.")
        return AREA


# Define a function to handle created text
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["text"] = update.message.text
    await update.message.reply_text("Please send me the photos.")
    return PHOTOS


# Define a function to handle created photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    photo_file_id = update.message.photo[-1].file_id
    user_data[user_id]["photos"].append(photo_file_id)
    await update.message.reply_text(
        "Photo received. You can send more photos or use /preview to see the ad preview."
    )
    return PHOTOS


# Define the preview command handler function
async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if user_id in user_data:
        data = user_data[user_id]
        district_hash = "_".join(data["district"].split())
        if int(data["price"]) // 10_000 * 10_000 == int(data["price"]):
            price_hash = int(data["price"])
        else:
            price_hash = (int(data["price"]) // 10_000 + 1) * 10_000

        text = (
            f"#{district_hash}, #under_{price_hash}\n\n"
            f"Rooms: {data['rooms']}\n"
            f"Price: {data['price']} AED/Year\n"
            f"Type: {data['type']}\n"
            f"Area: {data['area']} sqm\n"
            f"House Name: {data['house_name']}\n"
            f"District: {data['district']}\n\n"
            f"{data['text']}\n\n"
            f"Contact: @{data['username']}"
        )
        photos = data["photos"]

        # Create a list of InputMediaPhoto objects
        media = [
            InputMediaPhoto(media=photo, caption=(text if i == 0 else ""))
            for i, photo in enumerate(photos)
        ]

        # Send the preview with confirmation and edit buttons
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
    if user_id in user_data:
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
    if user_id in user_data:
        data = user_data[user_id]
        district_hash = "_".join(data["district"].split())
        if int(data["price"]) // 10_000 * 10_000 == int(data["price"]):
            price_hash = int(data["price"])
        else:
            price_hash = (int(data["price"]) // 10_000 + 1) * 10_000

        text = (
            f"#{district_hash}, #under_{price_hash}\n\n"
            f"Rooms: {data['rooms']}\n"
            f"Price: {data['price']} AED/Year\n"
            f"Type: {data['type']}\n"
            f"Area: {data['area']} sqm\n"
            f"House Name: {data['house_name']}\n"
            f"District: {data['district']}\n\n"
            f"{data['text']}\n\n"
            f"Contact: @{data['username']}"
        )
        photos = data["photos"]

        # Save the ad to the database
        ad_id = save_ad_to_db(user_id, data)

        if photos:
            # Create a list of InputMediaPhoto objects
            media = [
                InputMediaPhoto(media=photo, caption=(text if i == 0 else ""))
                for i, photo in enumerate(photos)
            ]
            # Send the created photos as a media group with the text as caption of the first photo
            await context.bot.send_media_group(chat_id=CHANNEL_USERNAME, media=media)

        # Clear the user data after posting
        del user_data[user_id]
        await query.message.reply_text(
            f"Your message has been posted. Ad ID: {ad_id}. Use /create to post another ad."
        )
        return ConversationHandler.END


# Define a function to handle the field to be edited
async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    field = update.message.text.lower().replace(" ", "_")
    if field in user_data[user_id]:
        user_data[user_id]["edit_field"] = field
        await update.message.reply_text(f"Please enter the new value for {field}:")
        return EDIT_VALUE
    else:
        await update.message.reply_text("Invalid field. Please choose a valid field.")
        return EDIT


# Define a function to handle the updated field value
async def update_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    field = user_data[user_id].get("edit_field")
    if field:
        user_data[user_id][field] = update.message.text
        del user_data[user_id]["edit_field"]
        await update.message.reply_text(f"{field} updated. Returning to preview...")
        return await preview(update, context)
    else:
        await update.message.reply_text("Error updating field. Please try again.")
        return EDIT


# Define the get_ad command handler function
async def get_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ad_id = int(context.args[0])
    ad = fetch_ad_by_id(ad_id)
    if ad:
        username, photos, rooms, price, type, area, house_name, district, text = ad
        ad_text = (
            f"{text}\n\n"
            f"Rooms: {rooms}\n"
            f"Price: {price} AED/year\n"
            f"Rent type: {type}\n"
            f"Area: {area} sqm\n"
            f"House Name: {house_name}\n"
            f"District: {district}\n\n"
            f"Contact: @{username}"
        )
        if photos:
            # Create a list of InputMediaPhoto objects
            media = [
                InputMediaPhoto(media=photo, caption=(ad_text if i == 0 else ""))
                for i, photo in enumerate(photos)
            ]
            # Send the ad photos as a media group with the text as caption of the first photo
            await update.message.reply_media_group(media=media)
    else:
        await update.message.reply_text("Ad not found.")
