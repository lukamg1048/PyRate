from disnake.ext import commands
from disnake import User as disnakeUser, Thread as disnakeThread, ChannelType

from db import DB
from models.snowflakes import User, Thread, Guild
from models.embed import Field, EmbedBuilder
from util import Interaction

class Threads(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ##############################################
    #
    # /thread Group
    #
    ##############################################
    @commands.slash_command(name="thread", dm_permission=False)
    async def thread(self, inter: Interaction):
        pass

    @thread.sub_command(
        name="create", 
        description="Creates a new thread between the caller and a specified user, then links it to PyRate."
    )
    async def thread_create(self, inter: Interaction, user2: disnakeUser):
        channel_to_create_in = (
            inter.channel
            if inter.channel.type == ChannelType.text 
            else inter.channel.parent
        )
        u1 = User(discord_id=inter.author.id)
        u2 = User(discord_id=user2.id)
        try:
            
            disnake_thread: disnakeThread = await channel_to_create_in.create_thread(
                name=f"{inter.author.name} and {user2.name}",
                type=ChannelType.public_thread
            )
            thread = Thread(
                guild=Guild(discord_id=inter.guild_id),
                thread_id=disnake_thread.id,
                user1=u1,
                user2=u2,
                next_user=u1
            )
            await DB.create_thread(thread=thread)
            await inter.response.send_message(f"Thread created successfully: {thread.mention}!")
            await disnake_thread.send(f"Thread created successfully between {u1.mention} and {u2.mention}!")
        except ValueError as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)

    @thread.sub_command(name="link")
    async def thread_link(self, inter: Interaction, user2: disnakeUser):
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
            await inter.response.send_message(f"Thread between {u1.mention} and {u2.mention} successfully linked to PyRate!")
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

    @thread.sub_command(
        name="waiting",
        description="Get a list of threads waiting on you in the current server",
    )
    async def thread_waiting(
        self,
        inter: Interaction,
    ):
        caller: User = User(inter.author.id)
        guild: Guild = Guild(inter.guild_id)
        threads = await DB.get_waiting_threads_by_user(caller, guild)
        if not threads:
            await inter.response.send_message("You're all caught up (in this server)!", ephemeral=True)
            return
        fields = []
        for thread in threads[:5]:
            other_user: disnakeUser = await self.bot.getch_user(thread.other_user.discord_id)
            fields.append(
                Field(
                    name=other_user.display_name,
                    value=thread.mention
                )
            )
        if len(threads) > 5:
            fields.append(Field(name="Plus", value=f"{len(threads) - 10} more..."))
        builder = EmbedBuilder(
            title=f"Threads waiting on {inter.author.display_name}",
            fields=fields,
        )
        await inter.response.send_message(embed=await builder.build())

    @thread.sub_command(name="delink", description="Delinks a thread from PyRate without deleting it.")
    async def thread_delink(self, inter: Interaction):
        try:
            thread = await DB.get_thread_by_id(thread_id=inter.channel_id)
            await DB.delink_thread(thread)
            await inter.response.send_message(f"Thread {thread.mention} successfully delinked!")
        except(ValueError) as e:
            await inter.response.send_message(f"Error: {e}", ephemeral=True)
            return

    # @thread.sub_command(name="delete", description="Delinks a thread from PyRate, and then deletes it.")
    # @commands.default_member_permissions(administrator=True)
    # async def thread_delete(self, inter: Interaction):
    #     try:
    #         thread = await DB.get_thread_by_id(thread_id=inter.channel_id)
    #         await DB.delink_thread(thread)
    #         await inter.channel.delete()
    #         await inter.response.send_message(f"Thread successfully deleted!")
    #     except(ValueError) as e:
    #         await inter.response.send_message(f"Error: {e}", ephemeral=True)
    #         return

def setup(bot: commands.Bot):
    bot.add_cog(Threads(bot))