from typing import List

from disnake.ext import commands
from disnake import Role as disnakeRole, User as disnakeUser

from util import Interaction
from db import DB
from cache import RoleCache
from models.snowflakes import User, Role, Thread, Guild
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
        rating: commands.Range[float, 1, 10.0],
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

    @commands.slash_command(name="role", dm_permission=False)
    @commands.default_member_permissions(manage_guild=True)
    async def role(self, inter: Interaction):
        pass

    @role.sub_command(name="register")
    async def role_register(self, inter: Interaction, role: disnakeRole):
        new_role = Role(discord_id=role.id)
        if new_role in RoleCache.fetch(inter.guild.id):
            await inter.response.send_message(f"{new_role.mention} is already in the list of moderator roles.", ephemeral=True)
            return
        
        await DB.create_mod_role(role=new_role, guild=Guild(inter.guild.id))
        await inter.response.send_message(f"{new_role.mention} has been added to the list of moderator roles.")
        RoleCache.refresh()

    @role.sub_command(name="remove")
    async def role_remove(self, inter: Interaction, role: disnakeRole):
        role_to_delete = Role(discord_id=role.id)
        if role_to_delete not in RoleCache.fetch(inter.guild.id):
            await inter.response.send_message(f"{role_to_delete.mention} is not in the list of moderator roles.", ephemeral=True)
            return
        
        await DB.remove_mod_role(role=role_to_delete)
        await inter.response.send_message(f"{role_to_delete.mention} has been removed from the list of moderator roles.")
        RoleCache.refresh()

def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))