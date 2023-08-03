from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Mentionable:
    discord_id: int

    @property
    def mention(self) -> str:
        return f"<@{self.discord_id}>"

    # Implicitly compares the discord_ids of two Mentionables
    # So, allows `if mentionable == mentionable:`
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.discord_id == other.discord_id

@dataclass
class User(Mentionable):
    # Implicitly print a User instance as their ID
    def __repr__(self) -> str:
        return str(self.discord_id)

@dataclass
class Role(Mentionable):
    discord_id: int
    
    @property
    def mention(self) -> str:
        return f"<@&{self.discord_id}>"
    
    @classmethod
    def parse_tuples(cls, rows: List[Tuple]) -> List["Role"]:
        return [
            cls(discord_id=row[0])
            for row in rows
        ]

@dataclass
class Guild:
    discord_id: int

    def __hash__(self):
        return hash(self.discord_id)

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

    @property
    def mention(self) -> str:
        return f"<#{self.thread_id}>"

    # Implicitly checks whether a given user is a part of the thread
    # So, allows `if user in thread:`
    def __contains__(self, user) -> bool:
        return (user == self.user1 or user == self.user2)


    @classmethod
    def parse_tuple(cls, row: Tuple) -> "Thread":
        return cls(
            thread_id=row[0],
            guild=Guild(row[1]),
            user1=User(discord_id=row[2]),
            user2=User(discord_id=row[3]),
            next_user=User(discord_id=row[4])
        )

    @classmethod
    def parse_tuples(cls, tuples: List[Tuple]) -> List["Thread"]:
        return [
            cls(
                thread_id=row[0],
                guild=Guild(row[1]),
                user1=User(discord_id=row[2]),
                user2=User(discord_id=row[3]),
                next_user=User(discord_id=row[4])
            )
            for row in tuples
        ]    
