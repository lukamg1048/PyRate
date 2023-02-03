from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class User:
    discord_id: int

    @property
    def mention(self) -> str:
        return f"<@{self.discord_id}>"

@dataclass
class Guild:
    discord_id: int

@dataclass
class Thread:
    thread_id: int
    guild: Guild
    user1: User
    user2: User
    next_user: User

    @classmethod
    def parse_tuple(cls, row: Tuple) -> "Thread":
        return cls(
            thread_id=row[0],
            guild=row[1],
            user1=User(discord_id=row[2]),
            user2=User(discord_id=row[3]),
            next_user=User(discord_id=row[4])
        )

    @classmethod
    def parse_tuples(cls, tuples: List[Tuple]) -> List["Thread"]:
        return [
            cls(
                thread_id=row[0],
                user1=User(discord_id=row[1]),
                user2=User(discord_id=row[2]),
                next_user=User(discord_id=row[3])
            )
            for row in tuples
        ]    
