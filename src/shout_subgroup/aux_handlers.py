from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Introduction command
    @param update:
    @param context:
    @return:
    """
    chat_id = update.effective_chat.id

    start_msg = """Welcome to the PingDem bot 📣️🤖!

I'm here to help you create subgroups and alert members.

Use the /help command to learn about what I can do.
"""

    await context.bot.send_message(chat_id=chat_id, text=start_msg)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command that shows how to use the bot
    @param update:
    @param context:
    @return:
    """
    chat_id = update.effective_chat.id

    help_text = f"""Welcome to the PingDem bot 📣️🤖!

Available commands:
/shout - Mentions all the members of the group chat or specified subgroup.
/group - Used to create or add members to a subgroup.
/list - Shows all existing subgroups.
/kick - Removes a member from a subgroup.
/delete - Removes a subgroup.
/help - Gives more detailed information about the bot.
"""
    await context.bot.send_message(chat_id=chat_id, text=help_text, parse_mode="markdown")
