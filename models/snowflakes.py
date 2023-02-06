from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class User:
    discord_id: int

    @property
    def mention(self) -> str:
        return f"<@{self.discord_id}>"

    # Implicitly compares the discord_ids of two User instances
    # So, allows `if user == other_user:`
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.discord_id == other.discord_id

    # Implicitly print a User instance as their ID
    def __repr__(self) -> str:
        return str(self.discord_id)

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

    @property
    def other_user(self) -> User:
        return (
            self.user1 
            if self.next_user == self.user2
            else self.user2
        )

    # Implicitly checks whether a given user is a part of the thread
    # So, allows `if user in thread:`
    def __contains__(self, user) -> bool:
        return (user == self.user1 or user == self.user2)


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
