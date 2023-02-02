from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
import sqlite3
from typing import List, Tuple

@dataclass
class User:
    discord_id: int

    @property
    def mention(self) -> str:
        return f"<@{self.discord_id}>"

@dataclass
class Thread:
    thread_id: int
    user1: User
    user2: User
    next_user: User

    @classmethod
    def parse_tuple(cls, row: Tuple) -> "Thread":
        return cls(
            thread_id=row[0],
            user1=User(discord_id=row[1]),
            user2=User(discord_id=row[2]),
            next_user=User(discord_id=row[3])
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

@dataclass
class Song:
    name: str
    artist: str

@dataclass
class Recommendation:
    song: Song
    rater: User 
    suggester: User 
    timestamp: datetime
    rating: int = -1 # The given rating of a song. For open recommendations, this is -1.
    is_closed: bool = False

    @classmethod
    def parse_tuples(cls, tuples: List[Tuple]) -> List["Recommendation"]:
        return [
            cls(
                song=Song(name=row[0], artist=row[1]),
                rater=User(discord_id=row[2]),
                suggester=User(discord_id=row[3]),
                timestamp=row[4],
                rating = row[5],
                is_closed = row[6]
            )
            for row in tuples
        ]

class DB():
    def __init__(self, truncate=False) -> None:
        self.con = sqlite3.connect("pyrate.db")
        self.cur = self.con.cursor()
        self.cur.execute('PRAGMA foreign_keys = ON')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS user(
            discord_id NUMERIC PRIMARY KEY NOT NULL
            );
        ''')
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS thread(
                thread_id NUMERIC PRIMARY KEY NOT NULL,
                user1_id NUMERIC NOT NULL,
                user2_id NUMERIC NOT NULL,
                next_user NUMERIC NOT NULL,
                FOREIGN KEY(user1_id) REFERENCES user (discord_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY(user2_id) REFERENCES user (discord_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            );
        ''')
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS song(
                song_name varchar NOT NULL COLLATE NOCASE,
                artist varchar NOT NULL COLLATE NOCASE,
                PRIMARY KEY(song_name, artist)
            );
        ''')
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS recommendation(
                song_name varchar NOT NULL COLLATE NOCASE,
                artist varchar NOT NULL COLLATE NOCASE,
                rater_id NUMERIC NOT NULL,
                suggester_id NUMERIC NOT NULL,
                timestamp text NOT NULL,
                rating NUMERIC DEFAULT -1,
                is_closed NUMERIC DEFAULT 0,
                FOREIGN KEY (song_name, artist) REFERENCES song (song_name, artist)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (rater_id) REFERENCES user (discord_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (suggester_id) REFERENCES user (discord_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            );
        ''')
        if truncate:
            self.cur.execute('DELETE FROM user')
            self.cur.execute('DELETE FROM song')
            self.cur.execute('DELETE FROM recommendation')

    async def _add_user(self, user: User) -> None:
        self.cur.execute('''INSERT INTO user VALUES(?)''', (user.discord_id,))
    async def _does_user_exist(self, user: User) -> bool:
        self.cur.execute('''SELECT * FROM user WHERE discord_id = ?''', (user.discord_id,))
        return bool(self.cur.fetchone())

    async def _add_song(self, song: Song) -> None:
        self.cur.execute('''INSERT INTO song VALUES(?, ?)''', (song.name, song.artist))
    async def _does_song_exist(self, song: Song) -> bool:
        self.cur.execute('''SELECT * FROM song WHERE song_name = ? and artist = ?''', (song.name, song.artist))
        return bool(self.cur.fetchone())

    async def _add_thread(self, thread: Thread) -> None:
        self.cur.execute(
            '''INSERT INTO thread VALUES(?, ?, ?, ?)''',
            (thread.thread_id, thread.user1, thread.user2, thread.next_user)
        )
    async def _does_thread_exist(self, thread: Thread) -> bool:
        self.cur.execute('''SELECT * FROM thread WHERE thread_id = ?''', (thread.thread_id,))
        return bool(self.cur.fetchone())

    async def _add_rec_manual(self, rec:Recommendation) -> None:
        self.cur.execute(
            '''INSERT INTO recommendation VALUES(?, ?, ?, ?, ?, ?, ?)''',
            (
                rec.song.name, 
                rec.song.artist, 
                rec.rater.discord_id, 
                rec.suggester.discord_id, 
                rec.timestamp, rec.rating, 
                rec.is_closed
            )
        )

    async def _create_open_rec(self, rec: Recommendation) -> None:
        self.cur.execute(
            '''INSERT INTO recommendation VALUES(?, ?, ?, ?, ?, -1, 0)''',
            (rec.song.name, rec.song.artist, rec.rater.discord_id, rec.suggester.discord_id, rec.timestamp)
        )

    async def _close_rec(self, rec: Recommendation) -> None:
        self.cur.execute('''
                UPDATE recommendation SET rating = ?, is_closed = 1 
                WHERE song_name = ? AND artist = ? AND rater_id = ? AND suggester_id = ?
            ''',
            (rec.rating, rec.song.name, rec.song.artist, rec.rater.discord_id, rec.suggester.discord_id)
        )

    async def _does_rating_exist(self, rec: Recommendation) -> bool:
        self.cur.execute('''
                SELECT * FROM recommendation 
                WHERE song_name = ? AND artist = ? AND rater_id = ? AND suggester_id = ? AND is_closed = 1
            ''',
            (rec.song.name, rec.song.artist, rec.rater.discord_id, rec.suggester.discord_id)
        )
        return bool(self.cur.fetchone())

    async def debug_fetch_db(self, which_db: str):
        match which_db:
            case "user":
                self.cur.execute('''SELECT * FROM user''')
            case "thread":
                self.cur.execute('''SELECT * FROM thread''')
            case "song":
                self.cur.execute('''SELECT * FROM song''')
            case "recommendation":
                self.cur.execute('''SELECT * FROM recommendation''')
        return self.cur.fetchall()

    # Create an open recommendation, and add any users, artists, and songs that are not currently stored.
    async def create_open_rec(self, rec: Recommendation) -> None:
        if not await self._does_user_exist(rec.rater):
            await self._add_user(rec.rater)
        if not await self._does_user_exist(rec.suggester):
            await self._add_user(rec.suggester)
        if not await self._does_song_exist(rec.song):
            await self._add_song(rec.song)

        await self._create_open_rec(rec) 
        self.con.commit()

    # Close an open recommendation by providing a rating. 
    async def close_rec(self, rec: Recommendation) -> None:
        if await self._does_rating_exist(rec):
            await self._close_rec(rec)
            self.con.commit()
        else:
            raise ValueError("Attempted to close a non-existent rec.")
        

    # Manually add a (most likely closed) rating
    async def add_rating_manual(self, rec: Recommendation) -> None:
        if not await self._does_user_exist(rec.rater):
            await self._add_user(rec.rater)
        if not await self._does_user_exist(rec.suggester):
            await self._add_user(rec.suggester)
        if not await self._does_song_exist(rec.song):
            await self._add_song(rec.song)
        if await self._does_rating_exist(rec):
            raise ValueError("Attempted to create a pre-existing rec.")
        else:
            await self._add_rec_manual(rec)
            self.con.commit()

    async def create_thread(self, thread: Thread) -> None:
        if await self._does_thread_exist(thread):
            raise ValueError("Attempted to create a pre-existing thread")
        else:
            await self._add_thread(thread)
            self.con.commit()

    async def get_thread_by_id(self, thread_id: int) -> Thread:
        self.cur.execute(
            '''SELECT * FROM thread where thread_id = ?''',
            (thread_id,)
        )
        return Thread.parse_tuple(self.cur.fetchone())


    async def flip_thread(self, thread: Thread, next_user: User) -> None:
        if await self._does_thread_exist(thread):
            self.cur.execute(
                '''UPDATE thread SET next_user = ? WHERE thread_id = ?''',
                (next_user, thread.thread_id)
            )
            self.con.commit()

    async def get_waiting_threads_by_user(self, user: User) -> List[Thread]:
        self.cur.execute('''
                SELECT * FROM thread WHERE next_user = ?
            ''',
            (user.discord_id,)
        )
        return Thread.parse_tuples(self.cur.fetchall())


    # These two functions fetch all recommendations for a specific rater, either closed or open.
    async def get_ratings_by_rater(self, rater: User, is_closed = 1) -> List[Recommendation]:
        self.cur.execute('''
                SELECT song_name, artist, rater_id, suggester_id, timestamp, rating, is_closed 
                FROM recommendation WHERE rater_id = ? AND is_closed = ?
            ''', 
            (rater.discord_id, is_closed)
        )
        # Parse elements into dataclass in schema order 
        return Recommendation.parse_tuples(self.cur.fetchall())

    async def get_open_recs_by_rater(self, rater: User) -> List[Recommendation]:
       return await self.get_ratings_by_rater(rater, is_closed=0)
    
    # Fetch all recommendations of a specific song
    async def get_ratings_by_song(self, song: Song) -> List[Recommendation]:
        self.cur.execute('''
                SELECT song_name, artist, rater_id, suggester_id, timestamp, rating, is_closed 
                FROM recommendation WHERE song_name = ? and artist = ? AND is_closed = 1
            ''', 
            (song.name, song.artist)
        )
        return Recommendation.parse_tuples(self.cur.fetchall())
    
    # Fetch all recommendations of a specific song
    async def get_ratings_by_artist(self, artist) -> List[Recommendation]:
        self.cur.execute('''
                SELECT song_name, artist, rater_id, suggester_id, timestamp, rating, is_closed 
                FROM recommendation WHERE artist = ? AND is_closed = 1
            ''', (artist,)
        )
        return Recommendation.parse_tuples(self.cur.fetchall())

    # Takes two user IDs and returns all ratings between the two
    async def get_ratings_by_pair(self, a: User, b: User) -> List[Recommendation]:
        self.cur.execute('''
                SELECT song_name, artist, rater_id, suggester_id, timestamp, rating, is_closed 
                FROM recommendation WHERE rater_id IN (:a, :b) and suggester_id in (:a, :b) AND is_closed = 1
            ''', 
            {"a": a.discord_id, "b": b.discord_id}
        )
        return Recommendation.parse_tuples(self.cur.fetchall())


    #takes two user IDs as inputs and returns all songs they have both rated
    async def get_overlap(self, rater_a: User, rater_b: User) -> List[Tuple[Recommendation]]:
        self.cur.execute('''
                SELECT 
                    a.song_name, a.artist, 
                    a.suggester_id, a.timestamp, a.rating_a, 
                    b.suggester_id, b.timestamp, b.rating_b
                    FROM (
                        SELECT max(rating) rating_a, song_name, artist, timestamp, rater_id, suggester_id 
                            FROM recommendation WHERE rater_id = ? AND is_closed = 1 GROUP BY song_name, artist
                        ) a
                        INNER JOIN (
                            SELECT max(rating) rating_b, song_name, artist, timestamp, rater_id, suggester_id 
                            FROM recommendation WHERE rater_id = ? AND is_closed = 1 GROUP BY song_name, artist
                        ) b
                ON a.song_name = b.song_name AND a.artist = b.artist
            ''', 
            (rater_a.discord_id, rater_b.discord_id)
        )
        return [
            (
                Recommendation(
                    song=Song(name=item[0], artist=item[1]),
                    rater=rater_a,
                    suggester=User(discord_id=item[2]),
                    timestamp=item[3],
                    rating=item[4],
                    is_closed=True
                ),
                Recommendation(
                    song=Song(name=item[0], artist=item[1]),
                    rater=rater_b,
                    suggester=User(discord_id=item[5]),
                    timestamp=item[6],
                    rating=item[7],
                    is_closed=True
                )
            )
            for item in self.cur.fetchall()
        ]


# Tests commented out to allow move to async.
# TODO: Make PyTest Async suite.
'''
if __name__ == "__main__":
    backEnd = DB(True)
    print("Running initial tests:")
    user1 = User(12345)
    backEnd._add_user(user1)
    print(backEnd._does_user_exist(user1))
    print(not backEnd._does_user_exist(User(58613)))
    user2 = User(3)
    backEnd._add_user(user2)
    print(backEnd._does_user_exist(user2))

    sandstorm = Song("Sandstorm", "Darude")
    backEnd._add_song(sandstorm)
    print(backEnd._does_song_exist(sandstorm))
    print(not backEnd._does_song_exist(Song("Sandstorm", "dadude")))
    print(backEnd._does_song_exist(sandstorm))
    rec1 = Recommendation(
        song=sandstorm, 
        rater=user1, 
        suggester=user2, 
        timestamp=datetime.now(),
        rating=10,
        is_closed=True
    )
    backEnd.add_rating_manual(rec1)
    print(backEnd._does_rating_exist(rec1))
    print(
        not backEnd._does_rating_exist(
            Recommendation(
                Song("Sandstorm", "DaDude"), 
                User(12345), 
                User(3),
                datetime.now(),
            )
        )
    )
    print("\n")


    #ID 1 suggests a few songs, they are rated
    backEnd.add_rating_manual(
        Recommendation(
            Song("Goodbye", "AREZRA"), 
            User(12345), 
            User(1), 
            timestamp=datetime.now(), 
            rating=10, 
            is_closed=True
        )
    )
    backEnd.add_rating_manual(
        Recommendation(
            Song("Goodbye", "AREZRA"), 
            User(2), 
            User(1),
            timestamp=datetime.now(), 
            rating=6, 
            is_closed=True
        )
    )
    backEnd.add_rating_manual(
        Recommendation(
            Song("Goodbye", "AREZRA"), 
            User(3), 
            User(1),
            timestamp=datetime.now(), 
            rating=8, 
            is_closed=True
        )
    )
    backEnd.add_rating_manual(
        Recommendation(
            Song("Goodbye", "AREZRA"), 
            User(4), 
            User(1),
            timestamp=datetime.now(), 
            rating=5, 
            is_closed=True
        )
    )

    #users suggest songs back
    backEnd.add_rating_manual(
        Recommendation(
            Song("Drowning", "AREZRA"), 
            User(1), 
            User(12345),
            timestamp=datetime.now(), 
            rating=8, 
            is_closed=True
        )
    )
    backEnd.add_rating_manual(
        Recommendation(
            Song("My Son John", "Smokey Bastard"), 
            User(1), 
            User(2),
            timestamp=datetime.now(), 
            rating=6, 
            is_closed=True
        )
    )
    backEnd.add_rating_manual(
        Recommendation(
            Song("Time Bomb", "Feint"), 
            User(1), 
            User(3),
            timestamp=datetime.now(), 
            rating=7, 
            is_closed=True
        )
    )
    backEnd.add_rating_manual(
        Recommendation(
            Song("Dead Inside", "Younger Hunger"), 
            User(1), 
            User(4),
            timestamp=datetime.now(), 
            rating=3, 
            is_closed=True
        )
    )
    
    #some inter-user rating goes on
    backEnd.add_rating_manual(
        Recommendation(
            Song("Drowning", "AREZRA"), 
            User(3), 
            User(2),
            timestamp=datetime.now(), 
            rating=8, 
            is_closed=True
        )
    )
    #Two ratings for the same song by the same user
    backEnd.add_rating_manual(
        Recommendation(
            Song("Drowning", "AREZRA"), 
            User(3), 
            User(4),
            timestamp=datetime.now(), 
            rating=7, 
            is_closed=True
        )
    )
    backEnd.add_rating_manual(
        Recommendation(
            Song("Dead Inside", "Younger Hunger"), 
            User(3), 
            User(2),
            timestamp=datetime.now(), 
            rating=5, 
            is_closed=True
        )
    )
    print("Ratings of Goodbye:")
    pprint(backEnd.get_ratings_by_song(Song("goodbye", "arezra")))
    print("Ratings of arezra:")
    pprint(backEnd.get_ratings_by_artist("arezra"))
    print("User 2's ratings:")
    pprint(backEnd.get_ratings_by_rater(User(2)))
    print("User 3's ratings:")
    pprint(backEnd.get_ratings_by_rater(User(3)))

    print("Ratings between users 2 and 3")
    pprint(backEnd.get_ratings_by_pair(User(2),User(3)))

    print("Overlap between 1 and 3")
    pprint(backEnd.get_overlap(User(1),User(3)))

    print("User 2's ratings:")
    pprint(backEnd.get_ratings_by_rater(User(2)))

    print("Overlap between 2 and 3")
    pprint(backEnd.get_overlap(User(2),User(3)))
'''
