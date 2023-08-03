from typing import Dict, List, Tuple
from dataclasses import dataclass

from db import DB
from models.snowflakes import Role

@dataclass
class RoleCache:
    roles: Dict[int, List[Role]] = None

    @classmethod
    def refresh(cls):
        rows: List[Tuple] = DB.get_mod_roles()
        cls.roles = {}
        for row in rows:
            role = Role(discord_id=row[0])
            if row[1] not in cls.roles.keys():
                cls.roles[row[1]] = []
            cls.roles[row[1]].append(role)
    
    @classmethod
    def fetch(cls, guild_id: int) -> List[Role]:
        return cls.roles.get(guild_id, [])