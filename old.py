import os
import sqlite3

from dotenv import load_dotenv
from telegram import InputMediaPhoto, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

# Temporary storage for user data
user_data = {}

# Connect to the SQLite database
conn = sqlite3.connect("ads.db", check_same_thread=False)
cursor = conn.cursor()

# Create the ads table if it doesn't exist
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        photos TEXT NOT NULL,
        rooms INTEGER,
        price REAL,
        type TEXT,
        area TEXT,
        house_name TEXT,
        district TEXT,
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)
conn.commit()

# Define states for the conversation
TEXT, ROOMS, PRICE, TYPE, AREA, HOUSE_NAME, DISTRICT, PHOTOS = range(8)


# Define the start command handler function
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to Dubai Rent Bot! Use /create to start creating data."
    )


# Define the create command handler function
async def create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    user_data[user_id] = {"text": "", "photos": [], "username": username}
    await update.message.reply_text("Please send me the text for your ad.")
    return TEXT


# Define a function to handle created text
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["text"] = update.message.text
    await update.message.reply_text("How many rooms?")
    return ROOMS


# Define a function to handle number of rooms
async def handle_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["rooms"] = int(update.message.text)
    await update.message.reply_text("What is the price?")
    return PRICE


# Define a function to handle price
async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["price"] = float(update.message.text)
    await update.message.reply_text("What is the type of the apartment?")
    return TYPE


# Define a function to handle type
async def handle_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["type"] = update.message.text
    await update.message.reply_text("What is the area of the apartment?")
    return AREA


# Define a function to handle area
async def handle_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["area"] = update.message.text
    await update.message.reply_text("What is the name of the house?")
    return HOUSE_NAME


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
    await update.message.reply_text("Please send me the photos.")
    return PHOTOS


# Define a function to handle created photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    photo_file_id = update.message.photo[-1].file_id
    user_data[user_id]["photos"].append(photo_file_id)
    await update.message.reply_text(
        "Photo received. You can send more photos or use /post to submit."
    )

    return PHOTOS


# Define a function to save ads to the database
def save_ad_to_db(user_id, data):
    photos_str = ",".join(
        data["photos"]
    )  # Store photo file_ids as a comma-separated string
    cursor.execute(
        "INSERT INTO ads (user_id, username, photos, rooms, price, type, area, house_name, district, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            data["username"],
            photos_str,
            data["rooms"],
            data["price"],
            data["type"],
            data["area"],
            data["house_name"],
            data["district"],
            data["text"],
        ),
    )
    ad_id = cursor.lastrowid
    conn.commit()
    return ad_id


# Define the post command handler function
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in user_data:
        data = user_data[user_id]
        text = (
            f"{data['text']}\n\n"
            f"Rooms: {data['rooms']}\n"
            f"Price: {data['price']}\n"
            f"Type: {data['type']}\n"
            f"Area: {data['area']}\n"
            f"House Name: {data['house_name']}\n"
            f"District: {data['district']}\n"
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
        await update.message.reply_text(f"Your message has been posted. Ad ID: {ad_id}")


# Define a function to fetch an ad by ID from the database
def fetch_ad_by_id(ad_id):
    cursor.execute(
        "SELECT username, photos, rooms, price, type, area, house_name, district, text FROM ads WHERE id = ?",
        (ad_id,),
    )
    ad = cursor.fetchone()
    if ad:
        username, photos_str, rooms, price, type, area, house_name, district, text = ad
        photos = photos_str.split(",")  # Convert comma-separated string back to list
        return username, photos, rooms, price, type, area, house_name, district, text
    return None


# Define the get_ad command handler function
async def get_ad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ad_id = int(context.args[0])
    ad = fetch_ad_by_id(ad_id)
    if ad:
        username, photos, rooms, price, type, area, house_name, district, text = ad
        ad_text = (
            f"{text}\n\n"
            f"Rooms: {rooms}\n"
            f"Price: {price}\n"
            f"Type: {type}\n"
            f"Area: {area}\n"
            f"House Name: {house_name}\n"
            f"District: {district}\n"
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


def main() -> None:
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Create a conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("create", create)],
        states={
            ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rooms)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_type)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_area)],
            HOUSE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_house_name)
            ],
            DISTRICT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_district)
            ],
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            PHOTOS: [MessageHandler(filters.PHOTO, handle_photo)],
        },
        fallbacks=[],
    )

    # Register the conversation handler
    application.add_handler(conv_handler)

    # Register the start command handler
    application.add_handler(CommandHandler("start", start))

    # Register the post command handler
    application.add_handler(CommandHandler("post", post))

    # Register the get_ad command handler
    application.add_handler(CommandHandler("get_ad", get_ad))

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()


if __name__ == "__main__":
    main()
