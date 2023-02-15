from disnake.ext import commands

from db import DB
from models.modal import RecommendModal

from util import Interaction, fetch_thread, validate_request, validate_request_recommender
from models.snowflakes import User


class Recommend(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
            thread = await fetch_thread(inter)
            await validate_request(inter, thread)
        except(ValueError) as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            return
        # Also check that there is no open rec:
        if await DB.does_thread_have_open_rec(thread):
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
            thread = await fetch_thread(inter)
            await validate_request(inter, thread)
        except(ValueError) as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            return
        if not await DB.get_open_rating_by_thread(thread):
            await inter.response.send_message("Error: There is no open recommendation to rate.", ephemeral=True)
            return
        rec = await DB.get_open_rating_by_thread(thread)
        rec.rating = rating
        await DB.close_rec(rec)
        await inter.response.send_message(f"{rec.suggester.mention}, your recommendation has been rated **{rec.rating}/10**. Any additional comments may be given above or below.")
    
    @commands.slash_command(name="clear_reccomendation", description="Clears your active recommendation", dm_permission=False)
    async def clear_rec(self, inter):
        try:
            thread = await fetch_thread(inter)
            print(f"Thread: {thread}")
        except(Exception) as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            return

        await validate_request_recommender(inter, thread)
        print("request validated")

        rec = await DB.get_open_rating_by_thread(thread)
        if not rec:
            await inter.response.send_message("Error: There is no open recommendation to clear.", ephemeral=True)
            return
        try:
            print("deleting rec")
            await DB._delete_rec(rec)
            print("deleted rec")
            await DB.flip_thread(thread=thread, next_user=User(inter.author.id))
        except(Exception) as e:
            await inter.response.send_message(f"Could not delete recommendation: {e}", ephemeral=True)
            return
        
        await inter.response.send_message (f"Deleted recommendation: {rec.song.name} by {rec.song.artist}")
        
    

        


def setup(bot: commands.Bot):
    bot.add_cog(Recommend(bot))