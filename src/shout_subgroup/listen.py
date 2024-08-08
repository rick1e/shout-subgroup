from telegram import Update
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.models import SubgroupModel, UserModel
from shout_subgroup.repository import (
    find_all_users_in_group_chat,
    find_group_chat_by_telegram_group_chat_id,
    insert_user,
    insert_group_chat
    )

async def listen_for_messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("listening to "+str(update.message))
    chat_id = update.effective_chat.id

    group_chat = await find_group_chat_by_telegram_group_chat_id(session, chat_id)
    if not group_chat:
        group_chat = await insert_group_chat(session, update.effective_chat)

    current_user = UserModel(
        telegram_user_id=update.message.from_user.id, 
        username=update.message.from_user.username, 
        first_name=update.message.from_user.first_name, 
        last_name=update.message.from_user.last_name)

    all_users = await find_all_users_in_group_chat(session, chat_id)
    all_telegram_user_ids = [x.telegram_user_id for x in all_users]
    
    print(current_user.telegram_user_id)
    print(all_telegram_user_ids)

    if current_user.telegram_user_id not in all_telegram_user_ids:
        added_user = await insert_user(session, current_user)
        group_chat.users.append(added_user)
        session.add(group_chat)
        session.commit()
        print(str(added_user.username)+" was added")
    return
