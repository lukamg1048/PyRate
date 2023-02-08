from __future__ import annotations

from dotenv import dotenv_values
from typing import Union

from disnake import ApplicationCommandInteraction, ModalInteraction
from db import DB

values = dotenv_values()
token = values.get("DISCORD_TOKEN")

Interaction = Union[ApplicationCommandInteraction, ModalInteraction]

from models.snowflakes import Thread, User

async def fetch_thread(inter: Interaction) -> Thread:
    # Need to check if the the command is being called from an established thread...
    return await DB.get_thread_by_id(thread_id=inter.channel_id)

async def validate_request(inter: Interaction, thread: Thread):
    # ...that the caller is a part of that thread...
    author = User(inter.author.id)
    if author not in thread:
        raise ValueError("You are not a member of the current thread.")
    # ...and that they're actually at bat.
    if author != thread.next_user:
        raise ValueError("It is not your turn to make or rate a recommendation.")