from config import config 
from functools import wraps

MISSING_PERMISSION_MESSAGE = 'Sorry, that command requires the "{permission}" privilege.'

def get_user_privilege(tg_user):
	priv = config['privileges'].get(str(tg_user.id))
	if priv == None:
		priv = config['privileges']['default']
	return priv

def user_has_privilege(tg_user, privilege):
	priv = get_user_privilege(tg_user)
	if priv.get(privilege):
		return True
	else:
		return False

def privileged_command(privilege):
	def deco(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			update = args[1]
			if user_has_privilege(update.message.from_user, privilege):
				return func(*args, **kwargs)
			else:
				update.message.reply_text(MISSING_PERMISSION_MESSAGE.format(
					permission=privilege
				))
		return wrapper
	return deco