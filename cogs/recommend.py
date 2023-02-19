from disnake.ext import commands

from db import DB
from models.snowflakes import User
from models.modal import RecommendModal
from models.song import Song

from util import Interaction, fetch_thread, validate_request, validate_request_recommender

######################################################
#
#   RECOMMENDATION COMMAND GROUP
#
######################################################
async def rec_new(inter: Interaction):
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

async def rec_rate(
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

async def rec_rerate(
    inter: Interaction, 
    song: str, 
    artist: str, 
    rating: commands.Range[1, 10.0]
):
    caller = User(inter.author.id)
    try:
        thread = await fetch_thread(inter)
    except(Exception) as e:
        await inter.response.send_message(f"Error: {e}", ephemeral=True)
        return

    if caller == thread.user1:
        other = thread.user2
    elif caller == thread.user2:
        other = thread.user1
    else:
        await inter.response.send_message(f"You are not a member of this thread.", ephemeral=True)
        return
    
    try:
        recs = await DB.get_ratings_by_song_and_pair(Song(song, artist), caller, other)
        if not recs:
            await inter.response.send_message(f"Error: cannot find {song} by {artist} in your ratings", ephemeral=True)
            return
    except(Exception) as e:
        await inter.response.send_message(f"Error: {e}", ephemeral=True)
        return
    if len(recs) > 1:
        await inter.response.send_message(f"Error: multiple ratings with for the same song in this thread", ephemeral=True)
        return
    rec = recs[0]
    rec.rating = rating
    await DB._close_rec(rec)
    await inter.response.send_message(f"{rec.suggester.mention}, your recommendation **{song}** has been re-rated **{rec.rating}/10**. Any additional comments may be given above or below.", allowed_mentions= False)
    

async def rec_clear(inter: Interaction):
    try:
        thread = await fetch_thread(inter)
    except(Exception) as e:
        await inter.response.send_message(f"Error: {e}", ephemeral=True)
        return
    await validate_request_recommender(inter, thread)
    rec = await DB.get_open_rating_by_thread(thread)
    if not rec:
        await inter.response.send_message("Error: There is no open recommendation to clear.", ephemeral=True)
        return
    try:
        await DB._delete_rec(rec)
        await DB.flip_thread(thread=thread, next_user=User(inter.author.id))
    except(Exception) as e:
        await inter.response.send_message(f"Could not delete recommendation: {e}", ephemeral=True)
        return
    await inter.response.send_message (f"Deleted recommendation: {rec.song.name} by {rec.song.artist}")


class Recommend(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ##############################################
    #
    # /rec Group
    #
    ##############################################
    @commands.slash_command(
        name="rec",
        dm_permission=False
    )
    async def rec(self, inter: Interaction):
        pass

    @rec.sub_command(name="new", description="Recommend a song to another user.")
    async def new(self, inter: Interaction):
        await rec_new(inter)

    @rec.sub_command(        
        name="rate",
        description="Rate and close an open recommendation."
    )
    async def rate(
        self, inter: 
        Interaction, 
        rating: commands.Range[1, 10.0]
    ):
        await rec_rate(inter, rating)

    @rec.sub_command(
        name="rerate",
        description="Updates a previous rating made by you",
    )
    async def rerate(
        self, inter: 
        Interaction, 
        song: str, 
        artist: str, 
        rating: commands.Range[1, 10.0]
    ):
        await rec_rerate(inter, song, artist, rating)

    @rec.sub_command(
        name="clear",
        description="Clears your active recommendation"
    )
    async def clear(self, inter: Interaction):
        await rec_clear(inter)


    ##############################################
    #
    # /rec Group Legacy Options
    #
    ##############################################

    # DEPRECATED, USE OF /REC NEW IS PREFERRED
    @commands.slash_command(
        name="recommend",
        description="Recommend a song to another user. Deprecated, use of /rec new is preferred.",
        dm_permission=False
    )
    async def new_legacy(
        self,
        inter: Interaction,
    ): 
       await rec_new(inter)
        
    # DEPRECATED, USE OF /REC RATE IS PREFERRED
    @commands.slash_command(
        name="rate",
        description="Rate and close an open recommendation. Deprecated, use of /rec rate is preferred.",
        dm_permission=False
    )
    async def rate_legacy(
        self,
        inter: Interaction,
        rating: commands.Range[1, 10.0]
    ):
        await rec_rate(inter, rating)

    # DEPRECATED, USE OF /REC RERATE IS PREFERRED
    @commands.slash_command(
        name="rerate",
        description="Updates a previous rating made by you. Deprecated, use of /rec rerate is preferred.",
        dm_permission=False
    )
    async def rerate_legacy(
        self,
        inter: Interaction,
        song: str,
        artist: str,
        rating: commands.Range[1, 10.0]
    ):
        await rec_rerate(inter, song, artist, rating)

    # DEPRECATED, USE OF /REC CLEAR IS PREFERRED
    @commands.slash_command(name="clear", dm_permission=False)
    async def clear_legacy(self, inter: Interaction):
        pass

    @clear_legacy.sub_command(
        name="recomendation", 
        description="Clears your active recommendation. Deprecated, use of /rec clear is preferred."
    )
    async def clear_legacy_sub_command(self, inter):
        await rec_clear(inter)

def setup(bot: commands.Bot):
    bot.add_cog(Recommend(bot))