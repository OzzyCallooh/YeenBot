import json
import requests
from urllib.parse import urlencode

from telegram import ParseMode
from telegram.ext import CommandHandler

from config import config
from util import make_e621_wiki_link, make_e621_pretty_tag_link_list
from blacklist_global import get_blacklisted_tags
import blacklist_user
import blacklist_chat


BL_TYPES = ['chat', 'global']

E621_TAG_BASE_QUERY = 'order:random'
E621_SCORE_MIN = 20
E621_LIMIT = 20
E621_FILE_TYPES = {'jpg', 'jpeg', 'gif', 'png', 'tif', 'bmp'}
E621_FILE_SIZE_LIMIT = 1024*1024*2
E621_URL_YIFF = 'https://e621.net/post/index.json'
E621_QUERY_TIMEOUT = 10
E621_IMAGE_TIMEOUT = 8
E621_HEADERS = {'user-agent': 'YeenBot/1.69 (by Ozzy Callooh)'}
E621_RATINGS = {'q', 'e', 's'}

def check_blacklist(bot, update, tags, bl={}):
	bad_tags = {'global': set(),'chat': set(), 'user': set(), 'ignore': set()}

	# Check for any bad tags, add to respective bad_tags set
	for tag in tags:
		for bl_type in BL_TYPES:
			if tag in bl[bl_type]:
				bad_tags[bl_type].add(tag)
	
	# Chat-blacklisted tags and globally blacklisted tags will prevent a query altogether
	if len(bad_tags['global'] | bad_tags['chat']) > 0:
		sorry_message = 'Sorry, at least one of those tags is on a /blacklist.'

		# Check global blacklist
		if len(bad_tags['global']) > 1:
			sorry_message += ' The tags {tag_list} are on the /globalblacklist.'.format(
				tag_list=make_e621_pretty_tag_link_list(list(bad_tags['global']))
			)
		elif len(bad_tags['global']) == 1:
			tag = list(bad_tags['global'])[0]
			sorry_message += ' The tag {tag} is on the /globalblacklist.'.format(
				tag=make_e621_wiki_link(tag, tag)
			)

		# Check chat blacklist
		if len(bad_tags['chat']) > 1:
			sorry_message += ' The tags {tag_list} are on this chat\'s /chatblacklist.'.format(
				tag_list=make_e621_pretty_tag_link_list(list(bad_tags['chat']))
			)
		elif len(bad_tags['chat']) == 1:
			tag = list(bad_tags['chat'])[0]
			sorry_message += ' The tag {tag} is on the /chatblacklist.'.format(
				tag=make_e621_wiki_link(tag, tag)
			)

		update.message.reply_text(sorry_message, ParseMode.MARKDOWN)
		return False
	return True

def is_valid_entry(entry):
	return \
		'tags' in entry and \
		'file_url' in entry and \
		'file_ext' in entry and entry['file_ext'] in E621_FILE_TYPES and \
		'file_size' in entry and entry['file_size'] <= E621_FILE_SIZE_LIMIT and \
		'status' in entry and entry['status'] == 'active' and \
		'rating' in entry and entry['rating'] in E621_RATINGS and \
		'md5' in entry

def get_entry_blacklisted_tags(entry, bl):
	return set(entry['tags'].split(' ')).intersection(bl['ignore'] | bl['user'] | bl['chat'] | bl['global'])

def e621_search(bot, update, tags, tags_ignore=[]):
	bl = {
		'ignore': set(tags_ignore),
		'user': set(blacklist_user.UserBlacklist.get_user_blacklist(update.message.from_user)),
		'chat': set(blacklist_chat.ChatBlacklist.get_chat_blacklist(update.message.chat)),
		'global': set(config['blacklist']['global'])
	}
	if not check_blacklist(bot, update, tags, bl=bl): return

	tag_query = E621_TAG_BASE_QUERY + ' '.join([''] + tags)
	url = E621_URL_YIFF + '?' + urlencode({
		'limit': E621_LIMIT, 'tags': tag_query
	})
	print('e621 Query: {query}'.format(query=tag_query))
	print('e621 URL: {url}'.format(url=url))

	update.message.reply_text('Performing [search]({url}), please wait...'.format(url=url), ParseMode.MARKDOWN)

	# For each explicitly queried tag, pretend it is not on the blacklist for just this query
	for tag in tags:
		if tag in bl['user']:
			bl['user'].remove(tag)

	# Send the reuqest
	entries = None
	try:
		r = requests.get(url, timeout=E621_QUERY_TIMEOUT, headers=E621_HEADERS)
		entries = r.json()
	except Exception as e:
		update.message.reply_text('Something went wrong while contacting e621.')
		print(e)
		return

	# Select an entry
	selected_entry = None
	num_valid = 0
	num_blacklisted = 0
	found_bl_tags = set()
	for i,entry in enumerate(entries):
		if is_valid_entry(entry):
			num_valid += 1
			entry_bl_tags = get_entry_blacklisted_tags(entry, bl)
			if len(entry_bl_tags) == 0:
				print('Selecting entry ' + str(i))
				selected_entry = entry
				break
			else:
				print('Entry ' + str(i) + ' had blacklisted tags: ' + ', '.join(entry_bl_tags))
				num_blacklisted += 1
				found_bl_tags |= entry_bl_tags
		else:
			print('Entry ' + str(i) + ' not valid:')
			print(json.dumps(entry))

	if selected_entry != None:
		update.message.reply_text('Selected: [file]({file_url})'.format(file_url=selected_entry['file_url']), parse_mode=ParseMode.MARKDOWN)
	else:
		update.message.reply_text('No result!')


def command_e621(bot, update, args):
	e621_search(bot, update, args)

def setup_dispatcher(dispatcher):
	dispatcher.add_handler(CommandHandler('e621', command_e621, pass_args=True))
