from disnake.ext import commands
from disnake import Embed, User as disnakeUser

from util import Interaction
from db import DB
from models.snowflakes import User, Guild



class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @commands.slash_command(
    #     name="debug_print_db"
    # )
    # async def print_db(self, inter: Interaction, which_db: str):
    #     ret = await DB.debug_fetch_db(which_db)
    #     await inter.response.send_message(ret)

    @commands.slash_command(
        name="queue",
        description="Get a list of all the threads waiting on you."
    )
    async def get_user_queue(self, inter: Interaction, user: disnakeUser = None, guild_id: str = None):
        target = User(user.id) if user else User(inter.author.id)
        username = user.display_name if user else inter.author.display_name
        guild: Guild = Guild(int(guild_id)) if guild_id else Guild(inter.guild.id) if inter.guild else None
        threads = await DB.get_waiting_threads_by_user(
            user=target,
            guild=guild
        )
        if len(threads) == 0:
            await inter.response.send_message(
                "There are no threads currently waiting on the given user.", 
                ephemeral=True
            )
            return            
        embed = Embed(title=f"Threads waiting on {username}")
        for index, thread in enumerate(threads, 1):
            embed.add_field(
                name=index,
                value=thread.mention,
                inline=True
            )
        await inter.response.send_message(
            embed=embed
        )

def setup(bot: commands.Bot):
    bot.add_cog(Misc(bot))