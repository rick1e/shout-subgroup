from telegram import Update
from telegram.ext import ContextTypes


async def remove_subgroup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Mock Delete Response")
    return
