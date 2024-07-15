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
    BUILDING,
    PHOTOS,
    PRICE,
    ROOMS,
    TEXT,
    TYPE,
    CHOOSING,
    TYPING_REPLY,
)
from edit_handlers import (
    edit_ad_start,
    edit_field,
    finish_editing,
    save_edit,
)
from create_handlers import (
    create,
    handle_area,
    handle_district,
    handle_building,
    handle_photo,
    handle_price,
    handle_rooms,
    handle_text,
    handle_type,
    save_ad,
)
from main_handlers import cancel, start
from myads_handlers import get_my_ads, view_ad_callback, post_ad_callback
from settings import BOT_TOKEN


def main() -> None:

    application = Application.builder().token(BOT_TOKEN).build()

    create_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("create", create)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_type)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
            BUILDING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_building)
            ],
            DISTRICT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_district)
            ],
            ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rooms)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_area)],
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            PHOTOS: [
                MessageHandler(filters.PHOTO, handle_photo),
                CommandHandler("save_ad", save_ad),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    edit_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_ad_start, pattern=r"^edit_ad_")],
        states={
            CHOOSING: [
                CallbackQueryHandler(edit_field, pattern=r"^edit_"),
                CallbackQueryHandler(finish_editing, pattern=r"^done$"),
            ],
            TYPING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(create_conv_handler)

    application.add_handler(edit_conv_handler)

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("get_my_ads", get_my_ads))

    application.add_handler(CallbackQueryHandler(view_ad_callback, pattern="^view_ad_"))
    application.add_handler(CallbackQueryHandler(post_ad_callback, pattern="^post_ad_"))

    application.run_polling()


if __name__ == "__main__":
    main()
