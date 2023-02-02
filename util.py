from dotenv import dotenv_values
from typing import Union

from disnake import ApplicationCommandInteraction, ModalInteraction

values = dotenv_values()
token = values.get("DISCORD_TOKEN")

Interaction = Union[ApplicationCommandInteraction, ModalInteraction]