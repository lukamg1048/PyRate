from disnake.ext import commands
from disnake import User as disnakeUser

from util import Interaction
from db import DB
from models.snowflakes import User, Thread, Guild
from models.song import Song
from models.recommendation import Recommendation

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="thread", dm_permission=False)
    async def thread(self, inter: Interaction):
        pass

    @thread.sub_command(name="create")
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
        try:
            await DB.create_thread(thread=thread)
            await inter.response.send_message(f"Thread successfully created between {u1.mention} and {u2.mention}!")
        except ValueError as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
        

    @thread.sub_command(name="next")
    async def thread_next(self, inter: Interaction):
        try:
            thread = await DB.get_thread_by_id(thread_id=inter.channel_id)
            await inter.response.send_message(f"The user at bat in this thread is {thread.next_user.mention}.", ephemeral=True)
        except(ValueError) as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            return

    @commands.slash_command(name="manual")
    async def manual(self, inter):
        pass
    
    @manual.sub_command(name="rating")
    async def add_rating(
        self, 
        inter: Interaction,
        song_name: str,
        artist: str,
        suggester: disnakeUser,
        rater: disnakeUser,
        rating: commands.Range[1, 10.0] = None,
    ):
        rec = Recommendation(
            song=Song(song_name, artist),
            rater=User(rater.id),
            suggester=User(suggester.id),
            guild=Guild(inter.guild_id),
            timestamp=inter.created_at,
            rating=rating,
            is_closed=1 if rating is not None else 0
        )
        try:
            await DB.add_rating_manual(rec)
            await inter.response.send_message(embed=await rec.get_embed())
        except ValueError as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))