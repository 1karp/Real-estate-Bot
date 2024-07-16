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
    BUILDING,
    CHOOSING,
    DISTRICT,
    PHOTOS,
    PRICE,
    ROOMS,
    TEXT,
    TYPING_REPLY,
)
from create_handlers import (
    back_button,
    create,
    handle_area,
    handle_building,
    handle_district,
    handle_photo,
    handle_price,
    handle_rooms,
    handle_text,
    save_ad,
)
from edit_handlers import edit_ad_start, edit_field, finish_editing, save_edit
from main_handlers import cancel, start
from myads_handlers import (
    edit_post_ad_callback,
    get_my_ads,
    post_ad_callback,
    view_ad_callback,
)
from settings import BOT_TOKEN


def main() -> None:

    application = Application.builder().token(BOT_TOKEN).build()

    create_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("create", create)],
        states={
            ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rooms)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_area)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
            BUILDING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_building)
            ],
            DISTRICT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_district)
            ],
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            PHOTOS: [
                MessageHandler(filters.PHOTO, handle_photo),
                CommandHandler("save_ad", save_ad),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(back_button, pattern="^back_to_"),
        ],
    )

    edit_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_ad_start, pattern=r"^edit_ad_")],
        states={
            CHOOSING: [
                CallbackQueryHandler(edit_field, pattern=r"^edit_"),
                CallbackQueryHandler(finish_editing, pattern=r"^save$"),
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
    application.add_handler(
        CallbackQueryHandler(edit_post_ad_callback, pattern="^edit_post_ad_")
    )

    application.run_polling()


if __name__ == "__main__":
    main()
