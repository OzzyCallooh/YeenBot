from config import config
from privileges import privileged_command
import database

import sin
import blacklist_user
import blacklist_chat

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

@privileged_command('operator')
def command_special(bot, update):
	print('/special')
	update.message.reply_text('Hello, master!')

def command_hello(bot, update):
	print('/hello')
	update.message.reply_text('Hello, world')
	sin.SinCounter.award_sin(update.message.from_user, 1)

def main():
	print('Yes hello, this is yeen')

	database.init()
	logging.basicConfig(level=logging.INFO)

	updater = Updater(token=config['telegram']['token'])
	dispatcher = updater.dispatcher

	# Global commands
	dispatcher.add_handler(CommandHandler('hello', command_hello))
	dispatcher.add_handler(CommandHandler('special', command_special))

	# Module commands
	sin.setup_dispatcher(dispatcher)
	blacklist_user.setup_dispatcher(dispatcher)
	blacklist_chat.setup_dispatcher(dispatcher)

	# Let's go
	updater.start_polling(clean=True)
	updater.idle()