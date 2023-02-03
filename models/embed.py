from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

from disnake import Embed, File, Colour

@dataclass
class Field:
    name: str
    value: Any
    inline: bool = True

    async def set(self, embed: Embed):
        return embed.add_field(name=self.name, value=self.value, inline=self.inline)

@dataclass
class EmbedBuilder:
    class Config:
        arbitrary_types_allowed = True

    title: str
    description: Optional[str]
    timestamp: Optional[datetime]
    fields: Optional[List[Field]]
    thumbnail_url: Optional[str]
    thumbnail_file: Optional[File]
    image: Optional[File]

    async def build(self) -> Embed:
        self.fields = self.fields if self.fields is not None else []
        embed = Embed(
            title=self.title,
            description=self.description,
            color=Colour.dark_teal(),
            timestamp=self.timestamp
            or datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")),
        )
        for field in self.fields:
            embed = await field.set(embed=embed)
        if self.thumbnail_url is not None:
            embed.set_thumbnail(url=self.thumbnail_url)
        elif self.thumbnail_file is not None:
            embed.set_thumbnail(file=self.thumbnail_file)
        if self.image is not None:
            embed.set_image(file=self.image)
        return embed
