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
            #print_exception(e)
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
            #print_exception(e)
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
            #print_exception(e)
            return
    
    @stats.sub_command(name="history")
    async def stats_history(
        self,
        inter: Interaction,
        other: disnakeUser
    ): 

        try:
            ratings = await DB.get_ratings_by_pair(User(inter.author.id), User(other.id))
            title = f"History Between {inter.author.name} and {other.name}"

            headers = "Song", "Artist", "Suggester", "Rater", "Rating"
            data = []
            
            #create a dictionary matching discord id to discord name
            users = {inter.author.id : inter.author.name, other.id : other.name}
            for rating in ratings:
                data.append((rating.song.name, rating.song.artist, users[rating.suggester.discord_id], users[rating.rater.discord_id], rating.rating))

            message = build_table(title, headers, data)
            await inter.response.send_message(message)
            return
        except Exception as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            #print_exception(e)
            return

    
    @commands.slash_command(name="leaderboard", dm_permission=False)
    async def leaderboard(self, inter: Interaction):
        pass

    @leaderboard.sub_command(name="max")
    async def leaderboard_max(
        self,
        inter: Interaction,
        rater: disnakeUser = None
    ): 


        try:
            if rater:
                ratings = await DB.get_max_ratings(User(rater.id))
                title = f"{rater.name}'s Highest Ratings"
            else:
                ratings = await DB.get_max_ratings()
                title = f"Highest Rated Suggestion Leaderboard"

            headers = "Song", "Artist", "Suggester", "Rater", "Rating"
            data = []
            for rating in ratings:
                s_user = await self.bot.getch_user(rating.suggester.discord_id)
                r_user = await self.bot.getch_user(rating.rater.discord_id)
                data.append((rating.song.name, rating.song.artist, s_user.name, r_user.name, rating.rating))
            message = build_table(title, headers, data)
            await inter.response.send_message(message)
            return
        except Exception as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            #print_exception(e)
            return
    
    @leaderboard.sub_command(name="average")
    async def leaderboard_average(
        self,
        inter: Interaction,
        rater: disnakeUser = None
    ): 


        try:
            if rater:
                tups = await DB.get_average_ratings(User(rater.id))
                title = f"{rater.name}'s Ratings Average Leaderboard"
            else:
                tups = await DB.get_average_ratings()
                title = f"Ratings Average Leaderboard"

            headers = "User", "Average Rating"
            data = []
            for tup in tups:
                s_user = await self.bot.getch_user(tup[1].discord_id)
                data.append((s_user.name, round(tup[0], 1)))
            if not data:
                raise Exception("No data found for given query")
            message = build_table(title, headers, data)
            await inter.response.send_message(message)
            return
        except Exception as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            #print_exception(e)
            return

    @leaderboard.sub_command(name="total")
    async def leaderboard_total(
        self,
        inter: Interaction,
        rater: disnakeUser = None
    ): 


        try:
            if rater:
                tups = await DB.get_total_ratings(User(rater.id))
                title = f"{rater.name}'s Total Points Leaderboard"
            else:
                tups = await DB.get_total_ratings()
                title = f"Total Points Leaderboard"

            headers = "User", "Total Points"
            data = []
            for tup in tups:
                s_user = await self.bot.getch_user(tup[1].discord_id)
                data.append((s_user.name, round(tup[0], 1)))
            message = build_table(title, headers, data)
            await inter.response.send_message(message)
            return
        except Exception as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            #print_except
        
        
      
def setup(bot: commands.Bot):
    bot.add_cog(Stats(bot))