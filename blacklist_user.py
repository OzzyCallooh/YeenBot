from config import config
from util import format_seconds
from database import Base, dbsession

import math
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from telegram.ext import CommandHandler

BLSTATUS_ACTIVE = 0
BLSTATUS_DELETED = 1

class UserBlacklist(Base):
	__tablename__ = 'blacklistuser'
	id = Column(Integer, primary_key=True)
	tg_user_id = Column(BigInteger, nullable=False)
	status = Column(Integer, default=BLSTATUS_ACTIVE)
	tag = Column(String(128), nullable=False)
	added = Column(DateTime, default=None, nullable=False)
	deleted = Column(DateTime, default=None, nullable=True)

	def __init__(self, tg_user, tag):
		self.tg_user_id = tg_user.id
		self.tag = tag
		self.status = BLSTATUS_ACTIVE
		self.added = datetime.now()
		self.deleted = None

	def delete(self):
		if self.status != BLSTATUS_DELETED:
			self.status = BLSTATUS_DELETED
			self.deleted = datetime.now()

	@staticmethod
	def get_user_blacklist(tg_user):
		tags = []
		session = dbsession()
		# Query
		bls = session.query(UserBlacklist)\
			.filter(UserBlacklist.tg_user_id == tg_user.id)\
			.filter(UserBlacklist.status == BLSTATUS_ACTIVE)\
			.all()
		for bl in bls:
			tags.append(bl.tag)
		session.close()
		return tags

def command_getbl(bot, update, args):
	tags = UserBlacklist.get_user_blacklist(update.message.from_user)
	
	if len(tags) > 0:
		update.message.reply_text('Your blacklisted tags: {}'.format(
			', '.join(tags)
		))
	else:
		update.message.reply_text('You have no blacklisted tags.')

def command_delbl(bot, update, args):
	if len(args) == 0:
		update.message.reply_text('Format: /deleteblacklist <tag>')
		return
	tag = args[0]
	session = dbsession()
	# Query
	bls = session.query(UserBlacklist)\
		.filter(UserBlacklist.tg_user_id == update.message.from_user.id)\
		.filter(UserBlacklist.tag == tag)\
		.filter(UserBlacklist.status == BLSTATUS_ACTIVE)\
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
		update.message.reply_text('Deleted tag from your blacklist: ' + tag)
	else:
		update.message.reply_text('You have not blacklisted tag: ' + tag)

def command_addbl(bot, update, args):
	if len(args) == 0:
		update.message.reply_text('Format: /addblacklist <tag>')
		return
	tag = args[0]
	session = dbsession()
	# Query for already-existing tag
	bl = session.query(UserBlacklist)\
		.filter(UserBlacklist.tg_user_id == update.message.from_user.id)\
		.filter(UserBlacklist.tag == tag)\
		.filter(UserBlacklist.status == BLSTATUS_ACTIVE)\
		.first()
	if bl:
		update.message.reply_text('Tag already blacklisted for you: ' + tag)
	else:
		bl = UserBlacklist(update.message.from_user, tag)
		session.add(bl)
		session.commit()
		update.message.reply_text('Added tag to your blacklist: ' + tag)
	session.close()

def setup_dispatcher(dispatcher):
	dispatcher.add_handler(CommandHandler('addbl', command_addbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('addblacklist', command_addbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('delbl', command_delbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('delblacklist', command_delbl, pass_args=True))

	dispatcher.add_handler(CommandHandler('getbl', command_getbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('mybl', command_getbl, pass_args=True))
	dispatcher.add_handler(CommandHandler('myblacklist', command_getbl, pass_args=True))
	