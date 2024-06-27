import os
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


@dataclass
class User:
    """Stores users information"""
    id: int
    username: str
    first_name: str

# Your bot's token
load_dotenv()
TOKEN = os.getenv('TELEGRAM_API_KEY')
group_members = {
    "test1" : User(
        id=0,
        username='Hulk',
        first_name=''
    ),
    "test2" : User(
        id=1,
        username='',
        first_name='Nick'
    )
}


    

def mention_user(user: User) -> str:
    mention = ""
    if user.username:
        mention = f"@{user.username}"
    else:
        mention = f"[{user.first_name}](tg://user?id={user.id})"

    return mention

def create_message_to_mention_members(members) -> str:
    shout = ""
    for member_key in members:
        shout += mention_user(members[member_key])+" "

    return shout

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'Hello {update.effective_user.first_name}')
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def shout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ## TODO ##
    # Get all members of the group chat
    all_members = group_members
    # Create a message that @ all members
    message = create_message_to_mention_members(all_members)
    # Send the message with all the @s
    await update.message.reply_text(message)

def main() -> None:
    print('Runninig ...')
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("shout", shout))

    app.run_polling()

if __name__ == '__main__':
    main()
