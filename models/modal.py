from disnake.ui import Modal, TextInput, Button
from disnake import TextInputStyle, Embed, ButtonStyle

from models.snowflakes import Thread, Guild
from models.song import Song
from models.recommendation import Recommendation
from util import ModalInteraction
from db import DB

class RecommendModal(Modal):
    def __init__(self, thread: Thread):
        self.thread = thread
        components = [
            TextInput(
                label="Song Name",
                custom_id="song_name",
                style=TextInputStyle.short
            ),
            TextInput(
                label="Artist",
                custom_id="artist",
                style=TextInputStyle.short
            ),
            TextInput(
                label="URL",
                custom_id="url",
                style=TextInputStyle.short,
                placeholder="A link to the song, preferably YouTube."
            )
        ]
        super().__init__(
            title="Recommend",
            custom_id=f"Recommend-{thread.user1}-{thread.user2}",
            components=components
        )

    async def callback(self, inter: ModalInteraction):
        song_name = inter.text_values.get('song_name')
        artist = inter.text_values.get('artist')
        url = inter.text_values.get('url')

        if not url.startswith("http") and not url.startswith('https') and not url.startswith('discord'):
            await inter.response.send_message("Invalid url provided. Ensure that it begins with `http://` or `https://`", ephemeral=True)
            return

        song = Song(name=song_name.casefold(), artist=artist.casefold())
        thread = await DB.flip_thread(thread=self.thread)

        rec = Recommendation(
            song=song,
            rater=self.thread.next_user,
            suggester=self.thread.other_user,
            guild=Guild(inter.guild_id),
            timestamp=inter.created_at,
        )
        await DB.create_open_rec(rec)
        
        await inter.response.send_message(
            rec.rater.mention,
            embed = Embed(
                title="New Recommendation",
                description=f'"{song_name.upper()}" by {artist.upper()}'
            ),
            components=[Button(label="Link", url=url, style=ButtonStyle.link)]
        )

class TableModal(Modal):
    def __init__(self, headers : list, data : list[list]):
        self.headers = headers
        self.data = data
        components = [
            TextInput(
                label="Song Name",
                custom_id="song_name",
                style=TextInputStyle.short
            ),
            TextInput(
                label="Artist",
                custom_id="artist",
                style=TextInputStyle.short
            ),
            TextInput(
                label="URL",
                custom_id="url",
                style=TextInputStyle.short,
                placeholder="A link to the song, preferably YouTube."
            )
        ]
        super().__init__(
            title="Recommend",
            custom_id=f"Recommend-{thread.user1}-{thread.user2}",
            components=components
        )

    async def callback(self, inter: ModalInteraction):
        song_name = inter.text_values.get('song_name')
        artist = inter.text_values.get('artist')
        url = inter.text_values.get('url')

        if not url.startswith("http") and not url.startswith('https') and not url.startswith('discord'):
            await inter.response.send_message("Invalid url provided. Ensure that it begins with `http://` or `https://`", ephemeral=True)
            return

        song = Song(name=song_name.casefold(), artist=artist.casefold())
        thread = await DB.flip_thread(thread=self.thread)

        rec = Recommendation(
            song=song,
            rater=self.thread.next_user,
            suggester=self.thread.other_user,
            guild=Guild(inter.guild_id),
            timestamp=inter.created_at,
        )
        await DB.create_open_rec(rec)
        
        await inter.response.send_message(
            rec.rater.mention,
            embed = Embed(
                title="New Recommendation",
                description=f'"{song_name.upper()}" by {artist.upper()}'
            ),
            components=[Button(label="Link", url=url, style=ButtonStyle.link)]
        )