import math
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from telegram import ParseMode
from telegram.ext import CommandHandler

from config import config
from util import format_seconds
from database import Base, dbsession
from util import make_e621_pretty_tag_link_list

BLSTATUS_ACTIVE = 0
BLSTATUS_DELETED = 1

class ChatBlacklist(Base):
	__tablename__ = 'blacklistchat'
	id = Column(Integer, primary_key=True)
	tg_chat_id = Column(BigInteger, nullable=False)
	creator_tg_user_id = Column(BigInteger, nullable=False)
	status = Column(Integer, default=BLSTATUS_ACTIVE)
	tag = Column(String(128), nullable=False)
	added = Column(DateTime, default=None, nullable=False)
	deleted = Column(DateTime, default=None, nullable=True)

	def __init__(self, tg_chat, creator_tg_user, tag):
		self.tg_chat_id = tg_chat.id
		self.creator_tg_user_id = creator_tg_user.id
		self.tag = tag
		self.status = BLSTATUS_ACTIVE
		self.added = datetime.now()
		self.deleted = None

	def delete(self):
		if self.status != BLSTATUS_DELETED:
			self.status = BLSTATUS_DELETED
			self.deleted = datetime.now()

	@staticmethod
	def get_chat_blacklist(tg_chat):
		tags = []
		session = dbsession()
		# Query
		bls = session.query(ChatBlacklist)\
			.filter(ChatBlacklist.tg_chat_id == tg_chat.id)\
			.filter(ChatBlacklist.status == BLSTATUS_ACTIVE)\
			.all()
		for bl in bls:
			tags.append(bl.tag)
		session.close()
		return tags

def command_getchatbl(bot, update, args):
	tags = ChatBlacklist.get_chat_blacklist(update.message.chat)
	
	if len(tags) > 0:
		update.message.reply_text('Blacklisted tags in this chat ({count}): {tag_list}'.format(
			count=len(tags),
			tag_list=make_e621_pretty_tag_link_list(tags)
		), ParseMode.MARKDOWN)
	else:
		update.message.reply_text('This chat has no blacklisted tags.')

def command_delchatbl(bot, update, args):
	if len(args) == 0:
		update.message.reply_text('Format: /delchatbl <tag>')
		return
	tag = args[0]
	session = dbsession()
	# Query
	bls = session.query(ChatBlacklist)\
		.filter(ChatBlacklist.tg_chat_id == update.message.chat.id)\
		.filter(ChatBlacklist.tag == tag)\
		.filter(ChatBlacklist.status == BLSTATUS_ACTIVE)\
		.all()
	# Delete
	n = 0
	for bl in bls:
		bl.delete()
		session.add(bl)
		n += 1
	session.commit()
	session.close()
	if n > 0:
		update.message.reply_text('Deleted tag from chat blacklist: ' + tag)
	else:
		update.message.reply_text('This chat does not have this tag blacklisted: ' + tag)

def command_addchatbl(bot, update, args):
	if len(args) == 0:
		update.message.reply_text('Format: /addchatbl <tag>')
		return
	tag = args[0]
	session = dbsession()
	# Query for already-existing tag
	bl = session.query(ChatBlacklist)\
		.filter(ChatBlacklist.tg_chat_id == update.message.chat.id)\
		.filter(ChatBlacklist.tag == tag)\
		.filter(ChatBlacklist.status == BLSTATUS_ACTIVE)\
		.first()
	if bl:
		update.message.reply_text('Tag already blacklisted in this chat: ' + tag)
	else:
		bl = ChatBlacklist(update.message.chat, update.message.from_user, tag)
		session.add(bl)
		session.commit()
		update.message.reply_text('Added tag to this chat\'s blacklist: ' + tag)
	session.close()

def setup_dispatcher(dispatcher):
	dispatcher.add_handler(CommandHandler('addchatbl', command_addchatbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('addchatblacklist', command_addchatbl, pass_args=True))
	
	dispatcher.add_handler(CommandHandler('delchatbl', command_delchatbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('delchatblacklist', command_delchatbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('remchatbl', command_delchatbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('remchatblacklist', command_delchatbl, pass_args=True))

	dispatcher.add_handler(CommandHandler('chatbl', command_getchatbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('chatblacklist', command_getchatbl, pass_args=True))
