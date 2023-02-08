from disnake.ext import commands

from util import Interaction

class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @commands.slash_command(
    #     name="debug_print_db"
    # )
    # async def print_db(self, inter: Interaction, which_db: str):
    #     ret = await DB.debug_fetch_db(which_db)
    #     await inter.response.send_message(ret)

def setup(bot: commands.Bot):
    bot.add_cog(Misc(bot))