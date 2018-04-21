from telegram.ext import CommandHandler


def command_bl(bot, update):
	update.message.reply_text('Blacklisted tags:')

def setup_dispatcher(dispatcher):
	dispatcher