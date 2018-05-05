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

def make_pretty_list_str(raw):
	result = ''
	if len(raw) == 0: return ''
	last_entry = raw[-1]
	for i in range(0, len(raw) - 1):
		result += str(raw[i])
		if i < len(raw) - 2:
			result += ', '
	if len(raw) > 1:
		result += ' and '
	result += str(last_entry)
	return result

def make_link(url, text):
	return '[{text}]({url})'.format(
		text=text,
		url=url
	)

def make_e621_wiki_link(page_title, text):
	return make_link(
		'https://e621.net/wiki/show/{page_title}'.format(
			page_title=page_title
		),
		text
	)

def make_e621_pretty_tag_link_list(tags, limit=None):
	listy = None
	if limit == None or len(tags) <= limit:
		listy = [make_e621_wiki_link(tag, tag) for tag in tags]
	else:
		listy = [make_e621_wiki_link(tag, tag) for tag in tags[:limit - 1]]
		listy.append('{} more'.format(len(tags) - limit + 1))
	return make_pretty_list_str(listy) if len(tags) > 0 else 'None'
