import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Your bot's token
load_dotenv()
TOKEN = os.getenv('TELEGRAM_API_KEY')

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! I am your bot.')

def mention_all(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    members = context.bot.get_chat_administrators(chat_id)
    
    mentions = []
    for member in members:
        user = member.user
        if not user.is_bot:
            mentions.append(f"@{user.username}")
    
    if mentions:
        update.message.reply_text(' '.join(mentions))
    else:
        update.message.reply_text('No members found.')

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("mention_all", mention_all))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGKILL
    updater.idle()

if __name__ == '__main__':
    main()
