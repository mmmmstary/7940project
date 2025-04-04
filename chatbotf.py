import os
import configparser
import requests
import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from ChatGPT_HKBU import HKBU_ChatGPT
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


global chatgpt

def equipped_chatgpt(update, context):
    global chatgpt
    reply_message = chatgpt.submit(update.message.text)
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Helping you helping you.')

def add(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    try:
        msg = context.args[0]  # /add keyword <-- this should store the keyword

        # 获取Firebase数据库引用
        ref = db.reference('keywords')
        # 获取当前关键词的计数，如果不存在则初始化为0
        current_count = ref.child(msg).get() or 0
        # 增加计数
        new_count = current_count + 1
        ref.child(msg).set(new_count)

        update.message.reply_text(f'You have said {msg} for {new_count} times.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')

def set_value(update: Update, context: CallbackContext) -> None:
    """Set a value in Firebase when the command /set is issued."""
    try:
        key = context.args[0]
        value_str = ' '.join(context.args[1:])
        try:
            value = int(value_str)
        except ValueError:
            update.message.reply_text('Usage: /set <key> <value>')
            return
        ref = db.reference('keywords')
        ref.child(key).set(value)
        update.message.reply_text(f'Set {key} to {value}.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <key> <value>')

def get_value(update: Update, context: CallbackContext) -> None:
    """Get a value from Firebase when the command /get is issued."""
    try:
        key = context.args[0]
        ref = db.reference('keywords')
        value = ref.child(key).get()
        if value:
            update.message.reply_text(f'The value for {key} is {value}.')
        else:
            update.message.reply_text(f'{key} does not exist.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /get <key>')


def delete_value(update: Update, context: CallbackContext) -> None:
    """Delete a value from Firebase when the command /delete is issued."""
    try:
        key = context.args[0]
        ref = db.reference('keywords')

        # 检查键是否存在
        if ref.child(key).get() is None:
            update.message.reply_text(f'{key} does not exist.')
            return
        # 如果存在则删除
        try:
            ref.child(key).delete()
            update.message.reply_text(f'Deleted {key}.')
        except Exception as e:
            update.message.reply_text(f'Error deleting {key}: {e}')
    except IndexError:
        update.message.reply_text('Usage: /delete <key>')

def hello(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /hello is issued."""
    try:
        update.message.reply_text('Good day,' + str(context.args[0]) + '!')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /hello <keyword>')

#def get_secret(secret_id, project_id):
#    """
#    获取 GCP Secret Manager 中的密钥
#    """
#    client = secretmanager.SecretManagerServiceClient()
#    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
#    response = client.access_secret_version(name=name)
#    return response.payload.data.decode("UTF-8")

def main():
    # 从环境变量获取配置文件路径
    config_path = os.getenv('CONFIG_PATH', './configGAI.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher


    # 从环境变量获取Firebase配置文件路径
    cred_path = os.getenv('FIREBASE_CRED_PATH', '/key/serviceAccountKey.json')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': config['FIREBASE']['DATABASE_URL']
    })

    # You can set this logging module, so you will know when
    # and why things do not work as expected Meanwhile, update your config.ini as:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    # Get the dispatcher to register handlers
    global chatgpt
    chatgpt = HKBU_ChatGPT()
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), equipped_chatgpt)
    dispatcher.add_handler(chatgpt_handler)
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("set", set_value))
    dispatcher.add_handler(CommandHandler("get", get_value))
    dispatcher.add_handler(CommandHandler("delete", delete_value))
    dispatcher.add_handler(CommandHandler("hello", hello))
    

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()