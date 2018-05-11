from config import config
from telegram import ParseMode
from telegram.ext import CommandHandler

from util import make_e621_pretty_tag_link_list
import blacklist_user
import blacklist_chat
from usagelog import logged_command

bl_global = sorted(config['blacklist']['global'])

def get_blacklisted_tags(user, chat):
	bl_user = blacklist_user.UserBlacklist.get_user_blacklist(user)
	bl_chat = blacklist_chat.ChatBlacklist.get_chat_blacklist(chat)
	return bl_user + bl_chat + bl_global

@logged_command('globalbl')
def command_globalbl(bot, update):
	reply = '*Global Blacklist* ({count} tags): '.format(count=len(bl_global))
	reply += make_e621_pretty_tag_link_list(bl_global)
	update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

@logged_command('bl')
def command_bl(bot, update):
	reply = '*Blacklisted Tags*:'

	bl_user = blacklist_user.UserBlacklist.get_user_blacklist(update.message.from_user)
	reply += '\n- /myblacklist: ' + make_e621_pretty_tag_link_list(bl_user, limit=3)

	bl_chat = blacklist_chat.ChatBlacklist.get_chat_blacklist(update.message.chat)
	reply += '\n- /chatblacklist: ' + make_e621_pretty_tag_link_list(bl_chat, limit=3)

	reply += '\n- /globalblacklist: ' + make_e621_pretty_tag_link_list(bl_global, limit=3)

	update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

@logged_command('blhelp')
def command_blhelp(bot, update):
	update.message.reply_text(
		'Blacklist commands:\n' +
		'/addbl <tag> - Blacklist a tag for you\n' +
		'/delbl <tag> - Unblacklist a tag for you\n' +
		'/getbl - Show blacklist\n'
	)

def setup_dispatcher(dispatcher):
	dispatcher.add_handler(CommandHandler('blacklist', command_bl, pass_args=False))
	dispatcher.add_handler(CommandHandler('bl', command_bl, pass_args=False))
	
	dispatcher.add_handler(CommandHandler('globalbl', command_globalbl, pass_args=False))
	dispatcher.add_handler(CommandHandler('globalblacklist', command_globalbl, pass_args=False))

	dispatcher.add_handler(CommandHandler('blhelp', command_blhelp))
	dispatcher.add_handler(CommandHandler('blacklisthelp', command_blhelp))