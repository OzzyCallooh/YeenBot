from config import config
from fasteners import InterProcessLock

ipl = InterProcessLock(config['lock_file'])

def lock_obtained():
	print('Lock obtained, starting YeenBot...')
	from yeenbot import main
	main()

def lock_not_obtained():
	print('Lock not obtained, exiting')

# Attempt to acquire the lock
acquired = ipl.acquire(blocking=False)
try:
	if acquired:
		lock_obtained()
	else:
		lock_not_obtained()
finally:
	if acquired:
		ipl.release()