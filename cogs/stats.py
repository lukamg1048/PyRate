from disnake.ext import commands
from disnake import User as disnakeUser, ui


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
            headers = "Song", "Artist", "Rater", "Rating"
            data = []
            for rating in ratings:
                data.append((rating.song.name, rating.song.artist, self.bot.get_user(rating.rater).name, rating.rating))

            message = build_table(title, headers, data)

            await inter.response.send_message(message)
            #await inter.response.send_message(f"Your max rating is {ratings}", ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            return
      
def setup(bot: commands.Bot):
    bot.add_cog(Stats(bot))