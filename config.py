"""

Configuration file loader. Usage:

from config import config
	if config['debug_mode']:
		print('Debug mode enabled!')

"""

import sys, json

config_fields = [
	'lock_file',
	'debug_mode',
	'privileges',
	'privileges.default',
	'sin',
	'sin.sin_limit',
	'sin.reset_minutes',
	'telegram',
	'telegram.token',
	'database',
	'database.uri',
	'database.trackModifications'
]

config_filename = 'config.json'
if len(sys.argv) >= 2:
	config_filename = sys.argv[1]
else:
	print('Provide the config filename as a command line argument')
	sys.exit(1)

# Exceptions
class ConfigError(Exception):
	pass

class MissingConfigError(ConfigError):
	def __init__(self, key):
		self.key = key
		self.message = 'Missing key in configuration: {}'.format(key)

# The global config map
config = None

try:
	# Open and read file
	with open(config_filename) as f:
		config = json.loads(f.read())

	# Verify required data exists
	for field in config_fields:
		base = config
		for s in field.split('.'):
			if s not in base:
				raise MissingConfigError(field)
			else:
				base = base[s]

except FileNotFoundError as e:
	print('Configuration file not found: {}'.format(config_filename))
	sys.exit(1)
except json.JSONDecodeError as e:
	print('Error while parsing config file: {}'.format(e))
	sys.exit(1)
except MissingConfigError as e:
	print('Configuration is missing key: {}'.format(e))
	sys.exit(1)
except Exception as e:
	print('Other error while reading configuration: {}'.format(e))
	sys.exit(1)

config['config_filename'] = config_filename
