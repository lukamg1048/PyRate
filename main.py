from bot import PyRate
from backend import DB
from util import token


db = DB()
bot = PyRate()

if __name__ == "__main__":
    bot.load_extension("cogs.misc")
    bot.load_extension("cogs.recommend")
    bot.run(token)
