from disnake import User as disnakeUser, Embed, ButtonStyle
from disnake.ext import commands

from disnake.ui import Button

from main import db
from backend import User, Thread, Song, Recommendation
from models.embed import EmbedBuilder

from util import Interaction


class Recommend(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="debug_print_db"
    )
    async def print_db(self, inter: Interaction, which_db: str):
        ret = await db.debug_fetch_db(which_db)
        await inter.response.send_message(ret)

    @commands.slash_command(
        name="recommend",
        description="Recommend a song to another user.",
        dm_permission=False
    )
    async def recommend(
        self,
        inter: Interaction,
        rater: disnakeUser,
        song_name: str,
        artist: str,
        link: str
    ): 
        suggester = User(discord_id=inter.author.id)
        rater = User(discord_id=rater.id)
        song = Song(name=song_name.casefold(), artist=artist.casefold())
        rec = Recommendation(
            song=song,
            rater=rater,
            suggester=suggester,
            timestamp=inter.created_at,
        )
        await db.create_open_rec(rec)
        await inter.response.send_message(
            rater.mention,
            embed = Embed(
                title="New Recommendation",
                description=f'"{song_name.upper()}" by {artist.upper()}'
            ),
            components=[Button(label="Link", url=link, style=ButtonStyle.link)]
        )

def setup(bot: commands.Bot):
    bot.add_cog(Recommend(bot))