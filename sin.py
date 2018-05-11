from config import config
from util import format_seconds, make_tg_user_url
from usagelog import logged_command
from privileges import privileged_command
from database import Base, dbsession

import math
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from telegram.ext import CommandHandler

sin_reset_td = timedelta(minutes=config['sin']['reset_minutes'])
class SinCounter(Base):
	__tablename__ = 'sincounter'
	id = Column(Integer, primary_key=True)
	tg_user_id = Column(BigInteger, nullable=False)
	first_seen = Column(DateTime, nullable=False)
	sin = Column(Integer, nullable=False)
	sin_avail = Column(Integer, nullable=False)
	sin_reset = Column(DateTime, nullable=False)
	last_sin = Column(DateTime)

	def __init__(self, tg_user_id):
		self.tg_user_id = tg_user_id
		self.first_seen = datetime.now()
		self.sin = 0
		self.reset_sin()

	def reset_sin(self):
		self.sin_avail = config['sin']['sin_limit']
		self.sin_reset = datetime.now() + sin_reset_td 

	def award_sin_with_limit(self, sin):
		if datetime.now() > self.sin_reset:
			self.reset_sin()
		sin = min(self.sin_avail, sin)
		self.sin += sin
		self.sin_avail -= sin
		self.last_sin = datetime.now()
		return sin

	@staticmethod
	def award_sin(tg_user, sin):
		session = dbsession()
		sc = session.query(SinCounter).filter(SinCounter.tg_user_id == tg_user.id).first()
		if not sc:
			sc = SinCounter(tg_user.id)
		sin = sc.award_sin_with_limit(sin)
		session.add(sc)
		session.commit()
		session.close()
		return sin

@logged_command('sin')
def command_sin(bot, update):
	print('/sin')
	tguid = update.message.from_user.id

	session = dbsession()
	sc = session.query(SinCounter).filter(SinCounter.tg_user_id == tguid).first()
	if sc:
		update.message.reply_text('You have {} sin points'.format(sc.sin))
	else:  
		update.message.reply_text('You haven\'t sinned...yet.')

@privileged_command('admin')
@logged_command('singet')
def command_singet(bot, update, args):
	if len(args) < 1:
		update.message.reply_text('Format: /singet <tg_user_id>')
		return

	# Parse arguments
	tg_user_id = None
	try:
		tg_user_id = int(args[0])
	except ValueError:
		update.message.reply_text('Invalid user id')
		return

	session = dbsession()
	sc = session.query(SinCounter).filter(SinCounter.tg_user_id == tg_user_id).first()
	reply = None
	if sc:
		reply = 'User ' + make_tg_user_url(tg_user_id) + ' has {} sin'.format(sc.sin)
	else:
		reply = 'User ' + make_tg_user_url(tg_user_id) + ' has not sin...yet.'
			
	update.message.reply_text(reply, parse_mode='MARKDOWN')
	session.close()

@privileged_command('admin')
@logged_command('sinset')
def command_sinset(bot, update, args):
	if len(args) < 2:
		update.message.reply_text('Format: /sinset <tg_user_id> <sin>')
		return

	# Parse arguments
	tg_user_id = None
	try:
		tg_user_id = int(args[0])
	except ValueError:
		update.message.reply_text('Invalid user id')
		return
	sin = None
	try:
		sin = int(args[1])
	except ValueError:
		update.message.reply_text('Invalid sin count')
		return

	session = dbsession()
	sc = session.query(SinCounter).filter(SinCounter.tg_user_id == tg_user_id).first()
	if not sc:
		sc = SinCounter(tg_user_id)
	sc.sin = sin
	session.add(sc)
	session.commit()
	session.close()
	update.message.reply_text('Set user ' + make_tg_user_url(tg_user_id) + ' sin to {}'.format(sin), parse_mode='MARKDOWN')

@privileged_command('admin')
@logged_command('sinadd')
def command_sinadd(bot, update, args):
	if len(args) < 2:
		update.message.reply_text('Format: /sinadd <tg_user_id> <sin>')
		return

	# Parse arguments
	tg_user_id = None
	try:
		tg_user_id = int(args[0])
	except ValueError:
		update.message.reply_text('Invalid user id')
		return
	sin = None
	try:
		sin = int(args[1])
	except ValueError:
		update.message.reply_text('Invalid sin count')
		return

	session = dbsession()
	sc = session.query(SinCounter).filter(SinCounter.tg_user_id == tg_user_id).first()
	if not sc:
		sc = SinCounter(tg_user_id)
	sc.sin += sin
	update.message.reply_text('User ' + make_tg_user_url(tg_user_id) + ' was given {} sin, they now have {}'.format(sin, sc.sin), parse_mode='MARKDOWN')
	session.add(sc)
	session.commit()
	session.close()

@privileged_command('admin')
@logged_command('sinlimitreset')
def command_sinlimitreset(bot, update, args):
	if len(args) < 1:
		update.message.reply_text('Format: /sinadd <tg_user_id>')
		return

	# Parse arguments
	tg_user_id = None
	try:
		tg_user_id = int(args[0])
	except ValueError:
		update.message.reply_text('Invalid user id')
		return

	session = dbsession()
	sc = session.query(SinCounter).filter(SinCounter.tg_user_id == tg_user_id).first()
	if sc:
		sc.reset_sin()
		update.message.reply_text('User ' + make_tg_user_url(tg_user_id) + ' sin limit has been reset.', parse_mode='MARKDOWN')
		session.add(sc)
		session.commit()
		session.close()
	else:
		update.message.reply_text('User ' + make_tg_user_url(tg_user_id) + ' has not sinned...yet.', parse_mode='MARKDOWN')

@privileged_command('admin')
@logged_command('sinlimit')
def command_sinlimit(bot, update):
	tguid = update.message.from_user.id

	session = dbsession()
	sc = session.query(SinCounter).filter(SinCounter.tg_user_id == tguid).first()
	if sc:
		dt = sc.sin_reset - datetime.now()
		reset_str = None
		secs = math.floor(dt.total_seconds())
		if secs <= 0:
			reset_str = 'reset {} ago'.format(format_seconds(-secs))
		else:
			reset_str = 'resetting in {}'.format(format_seconds(secs))
		update.message.reply_text('You have {} sin available, {}.'.format(
			sc.sin_avail,
			reset_str
		))
	else:
		update.message.reply_text('You haven\'t sinned...yet.')

def setup_dispatcher(dispatcher):
	dispatcher.add_handler(CommandHandler('sin', command_sin))
	dispatcher.add_handler(CommandHandler('sinlimit', command_sinlimit))
	dispatcher.add_handler(CommandHandler('sinset', command_sinset, pass_args=True))
	dispatcher.add_handler(CommandHandler('singet', command_singet, pass_args=True))
	dispatcher.add_handler(CommandHandler('sinadd', command_sinadd, pass_args=True))
	dispatcher.add_handler(CommandHandler('sinlimitreset', command_sinlimitreset, pass_args=True))
	#dispatcher.add_handler(CommandHandler('getsin', command_getsin))