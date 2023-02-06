from disnake import User as disnakeUser, Embed, ButtonStyle
from disnake.ext import commands

from disnake.ui import Button

from main import db
from models.snowflakes import User, Thread
from models.recommendation import Recommendation
from models.embed import EmbedBuilder
from models.modal import RecommendModal

from util import Interaction


class Recommend(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_thread(self, inter: Interaction) -> Thread:
        # Need to check if the the command is being called from an established thread...
        return await db.get_thread_by_id(thread_id=inter.channel_id)

    async def validate_request(self, inter: Interaction, thread: Thread):
        # ...that the caller is a part of that thread...
        author = User(inter.author.id)
        if author not in thread:
            raise ValueError("You are not a member of the current thread.")
        # ...and that they're actually at bat.
        if author != thread.next_user:
            raise ValueError("It is not your turn to make or rate a recommendation.")

    @commands.slash_command(
        name="get"
    )
    async def getopen(self, inter: Interaction):
        await inter.response.send_message(await db.get_open_rating_by_thread(await db.get_thread_by_id(thread_id=inter.channel_id)))

    @commands.slash_command(
        name="recommend",
        description="Recommend a song to another user.",
        dm_permission=False
    )
    async def recommend(
        self,
        inter: Interaction,
    ): 
        try:
            thread = await self.fetch_thread(inter)
            await self.validate_request(inter, thread)
        except(ValueError) as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            return
        # Also check that there is no open rec:
        if await db.does_thread_have_open_rec(thread):
            await inter.response.send_message("Error: There is already an open recommendation in this thread.", ephemeral=True)
        # Once we have confirmed the request is valid, 
        # we can actually create the recommednation.
        else:
            await inter.response.send_modal(RecommendModal(thread=thread))
        

    @commands.slash_command(
        name="rate",
        description="Rate and close an open recommendation.",
        dm_permission=False
    )
    async def rate(
        self,
        inter: Interaction,
        rating: commands.Range[1, 10.0]
    ):
        try:
            thread = await self.fetch_thread(inter)
            await self.validate_request(inter, thread)
        except(ValueError) as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            return
        if not await db.get_open_rating_by_thread(thread):
            await inter.response.send_message("Error: There is no open recommendation to rate.", ephemeral=True)
            return
        rec = await db.get_open_rating_by_thread(thread)
        rec.rating = rating
        await db.close_rec(rec)
        await inter.response.send_message(f"{rec.suggester.mention}, your recommendation has been rated **{rec.rating}/10**. Any additional comments may be given below.")
        


def setup(bot: commands.Bot):
    bot.add_cog(Recommend(bot))