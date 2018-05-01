from config import config

from telegram.ext import CommandHandler
import blacklist_user
import blacklist_chat

tags_global = config['blacklist']['global']

def get_blacklisted_tags(user, chat):
	tags_user = blacklist_user.UserBlacklist.get_user_blacklist(user)
	tags_chat = blacklist_chat.ChatBlacklist.get_chat_blacklist(chat)
	return tags_user + tags_chat + tags_global

def command_globalbl(bot, update):
	reply = 'Global Blacklist:\n'
	reply += ', '.join([tag for tag in tags_global])
	update.message.reply_text(reply)

def command_bl(bot, update):
	reply = 'The following tags are blacklisted here:\n'
	tags = get_blacklisted_tags(update.message.from_user, update.message.chat)
	reply += ', '.join([tag for tag in tags])
	update.message.reply_text(reply)

def setup_dispatcher(dispatcher):
	dispatcher.add_handler(CommandHandler('blacklist', command_bl, pass_args=False))
	dispatcher.add_handler(CommandHandler('bl', command_bl, pass_args=False))
	dispatcher.add_handler(CommandHandler('globalbl', command_globalbl, pass_args=False))
