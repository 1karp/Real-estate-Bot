import os

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from conversation_states import (
    AREA,
    DISTRICT,
    HOUSE_NAME,
    PHOTOS,
    PREVIEW,
    PRICE,
    ROOMS,
    TEXT,
    TYPE,
    EDIT,
    EDIT_VALUE,
)
from database import init_db
from handlers import (
    confirm,
    create,
    get_ad,
    handle_area,
    handle_district,
    handle_house_name,
    handle_photo,
    handle_price,
    handle_rooms,
    handle_text,
    handle_type,
    preview,
    edit,
    edit_field,
    update_field,
    start,
    restart,
)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


def main() -> None:
    # Initialize the database
    init_db()

    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Create a conversation handler with the states

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("create", create)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_type)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
            HOUSE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_house_name)
            ],
            DISTRICT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_district)
            ],
            ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rooms)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_area)],
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            PHOTOS: [
                MessageHandler(filters.PHOTO, handle_photo),
                CommandHandler("preview", preview),
            ],
            PREVIEW: [
                CallbackQueryHandler(confirm, pattern="^confirm$"),
                CallbackQueryHandler(edit, pattern="^edit$"),
            ],
            EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_field)],
        },
        fallbacks=[CommandHandler("restart", restart)],
    )

    # Register the conversation handler
    application.add_handler(conv_handler)

    # Register the start command handler
    application.add_handler(CommandHandler("start", start))

    # Register the get_ad command handler
    application.add_handler(CommandHandler("get_ad", get_ad))

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()


if __name__ == "__main__":
    main()
