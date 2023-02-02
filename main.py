from bot import PyRate
from backend import DB
from util import token


if __name__ == "__main__":
    db = DB()
    bot = PyRate()
    bot.run(token)
