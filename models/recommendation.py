from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple
from models.embed import EmbedBuilder, Field

from models.snowflakes import User, Guild
from models.song import Song

@dataclass
class Recommendation:
    song: Song
    rater: User 
    suggester: User
    guild: Guild 
    timestamp: datetime
    rating: int = -1 # The given rating of a song. For open recommendations, this is -1.
    is_closed: bool = False

    @classmethod
    def parse_tuple(cls, row: Tuple) -> List["Recommendation"]:
        return cls(
            song=Song(name=row[0], artist=row[1]),
            rater=User(discord_id=row[2]),
            suggester=User(discord_id=row[3]),
            guild=Guild(discord_id=row[4]),
            timestamp=row[5],
            rating = row[6],
            is_closed = row[7]
        )

    @classmethod
    def parse_tuples(cls, tuples: List[Tuple]) -> List["Recommendation"]:
        return [
            cls(
                song=Song(name=row[0], artist=row[1]),
                rater=User(discord_id=row[2]),
                suggester=User(discord_id=row[3]),
                guild=Guild(discord_id=row[4]),
                timestamp=row[5],
                rating = row[6],
                is_closed = row[7]
            )
            for row in tuples
        ]

    async def get_embed(self):
        return await EmbedBuilder(
            title="Manual Rating Added",
            description=f"{self.song.name.upper()} by {self.song.artist.upper()}",
            fields=[
                Field(name="Suggester", value=self.suggester.mention),
                Field(name="Rater", value=self.rater.mention),
                Field(name="Rating", value="None" if self.rating == -1 else self.rating)
            ]
        ).build()