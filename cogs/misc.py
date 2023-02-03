from disnake.ext import commands
from disnake import User as disnakeUser

from util import Interaction
from main import db
from models.snowflakes import User, Thread, Guild

class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="debug_print_db"
    )
    async def print_db(self, inter: Interaction, which_db: str):
        ret = await db.debug_fetch_db(which_db)
        await inter.response.send_message(ret)

    @commands.slash_command(name="add", dm_permission=False)
    async def add(self, inter: Interaction):
        pass

    @add.sub_command(name="thread")
    async def add_thread(self, inter: Interaction, user2: disnakeUser):
        u1 = User(discord_id=inter.author.id)
        u2 = User(discord_id=user2.id)
        thread = Thread(
            guild=Guild(discord_id=inter.guild_id),
            thread_id=inter.channel_id,
            user1=u1,
            user2=u2,
            next_user=u1
        )
        await db.create_thread(thread=thread)
        await inter.response.send_message(f"Thread successfully created between {u1.mention} and {u2.mention}!")

def setup(bot: commands.Bot):
    bot.add_cog(Misc(bot))