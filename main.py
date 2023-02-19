if __name__ == "__main__":
    from bot import PyRate
    from util import token
    from db import DB

    DB.setup()
    bot = PyRate()
    bot.load_extension("cogs.misc")
    bot.load_extension("cogs.recommend")
    bot.load_extension("cogs.admin")
    bot.load_extension("cogs.stats")
    bot.load_extension("cogs.threads")
    bot.run(token)
