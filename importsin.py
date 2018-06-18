# The original version of YeenBot stored sin counts in a JSON
# file called sin.json. This script uses a config file for this
# version of YeenBot that reads from sin.json and imports the counts
# into the database. sin.json contained one json object, the keys
# were Telegram user IDs and the values were the sin count.

import json

from config import config
from sin import SinCounter
from database import Base, dbsession, init

with open("sin.json") as f:
	imported_sin = json.loads(f.read())

userIdStrs = imported_sin.keys()
print("There are " + str(len(userIdStrs)) + " user ids")

init()
session = dbsession()
i = 0
for userIdStr in userIdStrs:
	userId = int(userIdStr)
	sc = session.query(SinCounter).filter(SinCounter.tg_user_id == userId).first()
	if not sc:
		sc = SinCounter(userId)
	sc.sin = imported_sin[userIdStr]
	session.add(sc)
	i = i + 1
	if i % 25 == 0:
		print("{} / {}".format(i, len(userIdStrs)))
session.commit()
session.close()
print("Done")