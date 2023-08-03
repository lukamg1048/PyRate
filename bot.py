import logging

import disnake
from disnake.ext import commands
from disnake.ext.commands import errors, CommandError
from disnake.ext.commands.context import Context

# Logging Setup
logger = logging.getLogger("disnake")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="./disnake.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


class PyRate(commands.Bot):
    def __init__(self):
        command_sync_flags = commands.CommandSyncFlags.default()
        command_sync_flags.sync_commands_debug = True
        intents = disnake.Intents.default()
        intents.message_content = True
        activity = disnake.Activity(type=disnake.ActivityType.listening, name="Some Bangers")
        command_prefix = "/"
        super().__init__(
            intents=intents,
            activity=activity,
            command_prefix=command_prefix,
            command_sync_flags=command_sync_flags,
        )

    async def on_command_error(self, context: Context, exception: CommandError) -> None:
        print(context.command.name)
        if context.command.name == "thread":
            await context.reply("You do not have the required permissions to execute this command.", ephemeral=True)
        return await super().on_command_error(context, exception)

    # Test/Init commands/events
    async def on_ready(self):

        print(f"We have logged in as {self.user}")