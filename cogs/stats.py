from disnake.ext import commands
from disnake import User as disnakeUser, ui

from traceback import print_exception
from util import build_table
from db import DB
from models.snowflakes import User, Thread, Guild
from models.song import Song
from models.recommendation import Recommendation
from util import Interaction, fetch_thread, validate_request


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="stats", dm_permission=False)
    async def stats(self, inter: Interaction):
        pass

    @stats.sub_command(name="max")
    async def stats_max(
        self,
        inter: Interaction,
        rater: disnakeUser = None
    ): 


        try:
            if rater:
                ratings = await DB.get_max_rating(User(inter.author.id), User(rater.id))
            else:
                ratings = await DB.get_max_rating(User(inter.author.id))
            if len(ratings) > 1:
                title = f"{inter.author.name}'s Highest Rated Recommendations"
            else:
                title = f"{inter.author.name}'s Highest Rated Recommendation"
            if rater:
                title += f" to {rater.name}"
            headers = "Song", "Artist", "Rater", "Rating"
            data = []
            for rating in ratings:
                discord_user = await self.bot.getch_user(rating.rater.discord_id)
                data.append((rating.song.name, rating.song.artist, discord_user.name, rating.rating))
            message = build_table(title, headers, data)
            await inter.response.send_message(message)
            return
            #await inter.response.send_message(f"Your max rating is {ratings}", ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            print_exception(e)
            return
    
    @stats.sub_command(name="average")
    async def stats_average(
        self,
        inter: Interaction,
        rater: disnakeUser = None
    ): 

        try:
            if rater:
                avg = await DB.get_average_rating(User(inter.author.id), User(rater.id))
                await inter.response.send_message(f"Your suggestions to {rater.name} are, on average, rated **{avg:.1f}**")
            else:
                avg = await DB.get_average_rating(User(inter.author.id))
                await inter.response.send_message(f"Your suggestions are, on average, rated **{avg:.1f}**")
            
            
        except Exception as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            print_exception(e)
            return
        
    @stats.sub_command(name="total")
    async def stats_total(
        self,
        inter: Interaction,
        rater: disnakeUser = None
    ): 

        try:
            if rater:
                total = await DB.get_total_rating(User(inter.author.id), User(rater.id))
                await inter.response.send_message(f"You have recieved **{total:.1f}** points from {rater.name}")
            else:
                total = await DB.get_total_rating(User(inter.author.id))
                await inter.response.send_message(f"You have recieved **{total:.1f}** points in total")
            
            
        except Exception as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            print_exception(e)
            return
      
def setup(bot: commands.Bot):
    bot.add_cog(Stats(bot))