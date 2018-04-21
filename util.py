"""
	Utility functions
"""
import math

def format_seconds(secs, short=True):
	hrs = math.floor(secs / 3600)
	secs = secs - hrs * 3600
	mins = math.floor(secs / 60)
	secs = secs - mins * 60
	s = ''
	if short:
		if hrs > 0:
			s += str(hrs) + 'h'
		if mins > 0:
			s += str(mins) + 'm'
		s += str(secs) + 's'
	else:
		if hrs > 0:
			s += str(hrs) + 'hrs'
		if mins > 0:
			s += str(mins) + 'mins'
		s += str(secs) + 'secs'
	return s
