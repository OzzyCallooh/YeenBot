import os
import json
import requests
from urllib.parse import urlencode
from pathlib import Path
from usagelog import logged_command

from telegram import ParseMode
from telegram.ext import CommandHandler

from config import config
from util import make_e621_wiki_link, make_e621_pretty_tag_link_list
from blacklist_global import get_blacklisted_tags
import blacklist_user
import blacklist_chat
from sin import SinCounter

BL_TYPES = ['chat', 'global']

download_path = Path(config['e621']['download_dir'])
def init_download_dir():
	download_path.mkdir(parents=True, exist_ok=True)
init_download_dir()

def check_blacklist(bot, update, tags, bl):
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

entry_keys = ['id','tags','file_url','file_ext','file_size','status','rating','md5']
def is_valid_entry(entry):
	for entry_key in entry_keys:
		if not entry_key in entry:
			print('Missing key: ' + entry_key)
			return False
	if entry['file_ext'] not in config['e621']['file_types']:
		print('Bad file type')
		return False
	if entry['file_size'] > config['e621']['file_size_limit']:
		print('Over size limit')
		return False
	if entry['status'] != 'active':
		print('Not active')
		return False
	if entry['rating'] not in config['e621']['ratings']:
		print('Bad rating')
		return False
	return True

def get_entry_blacklisted_tags(entry, bl):
	return set(entry['tags'].split(' ')).intersection(bl['ignore'] | bl['user'] | bl['chat'] | bl['global'])

def select_entry(entries, bl):
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
			print('Entry ' + str(i) + ' not valid')
			#print(json.dumps(entry))
	return selected_entry

def download_entry(entry):
	#print('Downloading entry')
	try:
		r = requests.get(entry['file_url'], stream=True, timeout=config['e621']['image_timeout'])
	except Exception as e: # TODO: add timeout?
		"""update.message.reply_text('Encountered problem while downloading image from e621. Here\'s a [link]({file_url}) instead.'.format(
			file_url=entry['file_url']
		), parse_mode=ParseMode.MARKDOWN)"""
		print('Download error.\n' + str(e))
		return

	if r.status_code != 200:
		return

	dl_path = Path(download_path, '{md5}.{file_ext}'.format(**entry))

	# Exit early if we've already downloaded this path
	if dl_path.exists():
		return dl_path

	# Write to file
	try:
		with dl_path.open(mode='wb') as f:
			for chunk in r.iter_content(1024):
				f.write(chunk)
	except OSError as e:
		print('OSError')
		return

	return dl_path

def send_entry(bot, update, dl_path):
	with dl_path.open(mode='rb') as f:
		bot.sendPhoto(
			chat_id=update.message.chat_id,
			photo=f,
			parse_mode=ParseMode.MARKDOWN
		)

def e621_search(bot, update, tags, tags_ignore=[]):
	bl = {
		'ignore': set(tags_ignore),
		'user': set(blacklist_user.UserBlacklist.get_user_blacklist(update.message.from_user)),
		'chat': set(blacklist_chat.ChatBlacklist.get_chat_blacklist(update.message.chat)),
		'global': set(config['blacklist']['global'])
	}
	if not check_blacklist(bot, update, tags, bl):
		print('Ignoring request due to blacklist')
		return

	tag_query = config['e621']['base_query'] + ' '.join([''] + tags)
	url = config['e621']['base_url'] + config['e621']['urls']['post/index'] + '?' + urlencode({
		'limit': config['e621']['query_entry_limit'], 'tags': tag_query
	})

	reply_msg = update.message.reply_text('Performing [search]({url}), please wait...'.format(url=url), ParseMode.MARKDOWN)

	# For each explicitly queried tag, pretend it is not on the blacklist for just this query
	for tag in tags:
		if tag in bl['user']:
			bl['user'].remove(tag)

	# Send the reuqest
	entries = None
	try:
		r = requests.get(url, timeout=config['e621']['query_timeout'], headers=config['e621']['headers'])
		entries = r.json()
	except Exception as e:
		reply_msg.edit_text('Something went wrong while contacting e621.')
		print(e)
		return

	# Select an entry
	entry = select_entry(entries, bl)
	if not entry:
		reply_msg.edit_text('No results.')
		return

	# Download entry
	dl_path = download_entry(entry)
	if not dl_path:
		reply_msg.edit_text('Image download failed')
		return

	# Send file
	reply_msg.edit_text('Sending...')
	send_entry(bot, update, dl_path)
	reply_msg.delete()

	SinCounter.award_sin(update.message.from_user, config['e621']['sin_award'])

	# Delete file
	dl_path.unlink()

@logged_command('e621')
def command_e621(bot, update, args):
	e621_search(bot, update, args)

def setup_dispatcher(dispatcher):
	dispatcher.add_handler(CommandHandler('e621', command_e621, pass_args=True))
