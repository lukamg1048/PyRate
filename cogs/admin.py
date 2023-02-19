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