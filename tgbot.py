import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackContext, Updater, MessageHandler, Filters, CommandHandler


def echo_handler(update: Update, context: CallbackContext):
    update.message.reply_text(update.message.text)

def main():
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")
    updater = Updater(tg_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text, echo_handler))

    updater.start_polling()


if __name__ == '__main__':
    main()