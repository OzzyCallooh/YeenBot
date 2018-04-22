# YeenBot

Hello! This is the repository for the YeenBot Telegram bot, written by me, [Ozzy Callooh](http://twitter.com/OzzyCallooh)! YeenBot is a [Telegram](http://telegram.org) bot whose purpose is primarily to be an [e621](http://e621.net) **(NSFW)** image roulette bot. I generally refer to him as my cyborg hyena son.

## Dependencies

YeenBot is built on Python 3.5. He uses several installed libraries, all of which can be installed using `pip`. You might need to have administrator privileges in order to do this.

```
pip install python-telegram-bot
pip install fasteners
pip install sqlalchemy
```

In addition, the configuration specifies a database URI. Your choice of database may have additional dependencies, for instance, MySQL (`pip install PyMySQL` should do the trick). However, Python has SQLite pre-packaged and the bot will work fine using that.

## Running the Telegram Bot

YeenBot runs off of configuration JSON files such as `sample.config.json`. This is also the included sample config, which describes each of the settings within \_\_COMMENT\_\_ keys. This file will include important details like the **Telegram bot token** and the **database URI** (used by SQLAlchemy). Perhaps you'll want `dev.config.json` and `prod.config.json`.

To start the bot, run `startup.py` with the configuration file name as the first and only command-line argument:

```
python startup.py dev.config.json
```

To stop the bot, send the interrupt signal (CTRL+C on Windows).

## Contributing

I don't typically include other's code in this project, but I'll be more than willing to consider pull requests! You should [send me a message on Telegram](http://t.me/OzzyC) if you're interested.
