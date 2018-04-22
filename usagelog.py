from database import Base, dbsession
from privileges import privileged_command

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from telegram.ext import CommandHandler

MAX_MESSAGE_LEN = 512
DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'

class UsageLog(Base):
	__tablename__ = 'usagelog'
	id = Column(Integer, primary_key=True)
	tg_user_id = Column(BigInteger, nullable=True)
	recorded = Column(DateTime, nullable=False)
	message = Column(String(MAX_MESSAGE_LEN), nullable=False)
	command = Column(String(128), nullable=True)
	result = Column(Integer, nullable=True)

	def __init__(self, message, tg_user=None, command=None, result=None):
		if tg_user != None:
			self.tg_user_id = tg_user.id
		else:
			self.tg_user_id = None
		self.command = command
		self.recorded = datetime.now()
		self.message = message[:MAX_MESSAGE_LEN]
		self.result = result

	def __str__(self):
		return '<Log[{id}]:{tg_user_id}:{command}>'.format(
			id=self.id,
			tg_user_id=self.tg_user_id,
			command=self.command
		)

def log_simple(text, tg_user=None):
	session = dbsession()
	session.add(UsageLog(text, tg_user=tg_user))
	session.commit()
	session.close()

def log_command(command, bot, update, result=None, message=None):
	session = dbsession()
	if not message:
		message = update.message.text
	log = UsageLog(message, tg_user=update.message.from_user, command=command, result=result)
	session.add(log)
	session.commit()
	session.close()

@privileged_command('operator')
def command_note(bot, update):
	if len(update.message.text) <= 6:
		update.message.reply_text('Format: /note <text>')
		return
	log_command('note', bot, update, message=update.message.text[6:])
	update.message.reply_text('Note recorded')

@privileged_command('operator')
def command_log(bot, update, args):
	session = dbsession()

	s = None
	if len(args) >= 1:
		if args[0] == 'user':
			i = None
			try:
				if args[1] == 'me':
					i = update.message.from_user.id
				else:
					i = int(args[1])
			except ValueError:
				pass
			if i != None:
				logs = session.query(UsageLog).filter(UsageLog.tg_user_id == i).order_by(UsageLog.recorded.desc()).limit(8).all()
				if len(logs) > 0:
					s = 'Recent Log for [{tg_user_id}](tg://user?id={tg_user_id}):'.format(tg_user_id=i)
					for log in logs:
						if log.command != None:
							s += '\n`[{id}]`: {command}'.format(
								id=log.id, command=log.command)
						else:
							s += '\n`[{id}]`: {message}'.format(
								id=log.id, command=log.message)
				else:
					s = 'No logs with that user id'
			else:
				s = 'Invalid user id'
		elif args[0] == 'entry':
			i = None
			try:
				i = int(args[1])
			except ValueError:
				pass
			if i != None:
				log = session.query(UsageLog).filter(UsageLog.id == i).one()
				if log:
					s = '*Recorded*: {}'.format(log.recorded.strftime(DATETIME_FORMAT))
					if log.tg_user_id != None:
						s += '\n*User:* [{tg_user_id}](tg://user?id={tg_user_id})'.format(tg_user_id=log.tg_user_id)
					if log.command != None:
						s += '\n*Command:* {}'.format(log.command)
					s += '\n*Message:*\n{}'.format(log.message)
				else:
					s = 'Unknown entry number'
			else:
				s = 'Invalid entry number'
	else:
		s = 'Recent Log:'
		logs = session.query(UsageLog).order_by(UsageLog.recorded.desc()).limit(8).all()
		for log in logs:
			s += '\n`[{}]`: '.format(log.id)
			if log.tg_user_id != None:
				s += '[{tg_user_id}](tg://user?id={tg_user_id}): '.format(
					tg_user_id=log.tg_user_id
				)
			if log.command != None:
				s += '/{}'.format(log.command)
			else:
				s += '{}'.format(log.message)
	
	update.message.reply_text(s, parse_mode='MARKDOWN')

def setup_dispatcher(dispatcher):
	dispatcher.add_handler(CommandHandler('log', command_log, pass_args=True))
	dispatcher.add_handler(CommandHandler('note', command_note))