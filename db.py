from datetime import datetime
from pprint import pprint
import sqlite3
from typing import List, Optional, Tuple, overload

from models.snowflakes import User, Guild, Thread
from models.song import Song
from models.recommendation import Recommendation

class DB():

    @classmethod
    def setup(cls, truncate=False) -> None:
        cls.con = sqlite3.connect("pyrate.db")
        cls.cur = cls.con.cursor()
        cls.cur.execute('PRAGMA foreign_keys = ON')
        cls.cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
                discord_id NUMERIC PRIMARY KEY NOT NULL
            );
        ''')
        cls.cur.execute('''
            CREATE TABLE IF NOT EXISTS thread(
                thread_id NUMERIC PRIMARY KEY NOT NULL,
                guild_id NUMERIC NOT NULL,
                user1_id NUMERIC NOT NULL,
                user2_id NUMERIC NOT NULL,
                next_user NUMERIC NOT NULL,
                FOREIGN KEY(user1_id) REFERENCES user (discord_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY(user2_id) REFERENCES user (discord_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
                FOREIGN KEY (next_user) REFERENCES user (discord_id) 
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE
            );
        ''')
        cls.cur.execute('''
            CREATE TABLE IF NOT EXISTS song(
                song_name varchar NOT NULL COLLATE NOCASE,
                artist varchar NOT NULL COLLATE NOCASE,
                PRIMARY KEY(song_name, artist)
            );
        ''')
        cls.cur.execute('''
            CREATE TABLE IF NOT EXISTS recommendation(
                song_name varchar NOT NULL COLLATE NOCASE,
                artist varchar NOT NULL COLLATE NOCASE,
                rater_id NUMERIC NOT NULL,
                suggester_id NUMERIC NOT NULL,
                guild_id NUMERIC NOT NULL,
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
            cls.cur.execute('DELETE FROM user')
            cls.cur.execute('DELETE FROM song')
            cls.cur.execute('DELETE FROM recommendation')

    @classmethod
    async def _add_user(cls, user: User) -> None:
        cls.cur.execute('''INSERT INTO user VALUES(?)''', (user.discord_id,))

    @classmethod
    async def _does_user_exist(cls, user: User) -> bool:
        cls.cur.execute('''SELECT * FROM user WHERE discord_id = ?''', (user.discord_id,))
        return bool(cls.cur.fetchone())

    @classmethod
    async def _add_song(cls, song: Song) -> None:
        cls.cur.execute('''INSERT INTO song VALUES(?, ?)''', (song.name, song.artist))
    
    @classmethod
    async def _does_song_exist(cls, song: Song) -> bool:
        cls.cur.execute('''SELECT * FROM song WHERE song_name = ? and artist = ?''', (song.name, song.artist))
        return bool(cls.cur.fetchone())

    @classmethod
    async def _add_thread(cls, thread: Thread) -> None:
        cls.cur.execute(
            '''INSERT INTO thread VALUES(?, ?, ?, ?, ?)''',
            (thread.thread_id, thread.guild.discord_id, thread.user1.discord_id, thread.user2.discord_id, thread.next_user.discord_id)
        )

    @classmethod
    # Can be used with either a thread object or a thread id int
    async def _does_thread_exist(cls, *, thread_id: int = None, thread: Thread = None) -> bool:
        cls.cur.execute('''SELECT * FROM thread WHERE thread_id = ?''', (thread_id or thread.thread_id,))
        return bool(cls.cur.fetchone())

    @classmethod
    async def _add_rec_manual(cls, rec:Recommendation) -> None:
        cls.cur.execute(
                '''INSERT INTO recommendation VALUES(?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    rec.song.name, 
                    rec.song.artist, 
                    rec.rater.discord_id, 
                    rec.suggester.discord_id,
                    rec.guild.discord_id,
                    rec.timestamp, 
                    rec.rating, 
                    rec.is_closed
                )
            )

    @classmethod
    async def _create_open_rec(cls, rec: Recommendation) -> None:
        cls.cur.execute(
            '''INSERT INTO recommendation VALUES(?, ?, ?, ?, ?, ?, -1, 0)''',
            (rec.song.name, rec.song.artist, rec.rater.discord_id, rec.suggester.discord_id, rec.guild.discord_id, rec.timestamp)
        )

    @classmethod
    async def _close_rec(cls, rec: Recommendation) -> None:
        cls.cur.execute('''
                UPDATE recommendation SET rating = ?, is_closed = 1 
                WHERE song_name = ? AND artist = ? AND rater_id = ? AND suggester_id = ? AND guild_id = ?
            ''',
            (rec.rating, rec.song.name, rec.song.artist, rec.rater.discord_id, rec.suggester.discord_id, rec.guild.discord_id)
        )
    @classmethod
    async def _delete_rec(cls, rec: Recommendation) -> None:
        cls.cur.execute('''
                DELETE FROM recommendation
                WHERE song_name = ? AND artist = ? AND rater_id = ? AND suggester_id = ? AND guild_id = ?
            ''',
            (rec.song.name, rec.song.artist, rec.rater.discord_id, rec.suggester.discord_id, rec.guild.discord_id)
        )

    @classmethod
    async def _does_rating_exist(cls, rec: Recommendation, is_closed: int = 1) -> bool:
        cls.cur.execute('''
                SELECT * FROM recommendation 
                WHERE song_name = ? AND artist = ? AND rater_id = ? AND suggester_id = ? AND guild_id = ? AND is_closed = ?
            ''',
            (rec.song.name, rec.song.artist, rec.rater.discord_id, rec.suggester.discord_id, rec.guild.discord_id, is_closed)
        )
        return bool(cls.cur.fetchone())

    @classmethod
    async def debug_fetch_db(cls, which_db: str):
        match which_db:
            case "user":
                cls.cur.execute('''SELECT * FROM user''')
            case "thread":
                cls.cur.execute('''SELECT * FROM thread''')
            case "song":
                cls.cur.execute('''SELECT * FROM song''')
            case "recommendation":
                cls.cur.execute('''SELECT * FROM recommendation''')
        return cls.cur.fetchall()

    @classmethod
    async def does_thread_have_open_rec(cls, thread: Thread) -> bool:
        cls.cur.execute('''
                SELECT * FROM recommendation
                WHERE rater_id = ? AND suggester_id = ? AND is_closed = 0
            ''',
            (thread.next_user.discord_id, thread.other_user.discord_id)
        )
        return bool(cls.cur.fetchone())

    # Create an open recommendation, and add any users, artists, and songs that are not currently stored.
    @classmethod
    async def create_open_rec(cls, rec: Recommendation) -> None:
        if not await cls._does_user_exist(rec.rater):
            await cls._add_user(rec.rater)
        if not await cls._does_user_exist(rec.suggester):
            await cls._add_user(rec.suggester)
        if not await cls._does_song_exist(rec.song):
            await cls._add_song(rec.song)

        await cls._create_open_rec(rec) 
        cls.con.commit()

    # Close an open recommendation by providing a rating. 
    @classmethod
    async def close_rec(cls, rec: Recommendation) -> None:
        if await cls._does_rating_exist(rec, is_closed = 0):
            await cls._close_rec(rec)
            cls.con.commit()
        else:
            raise ValueError("Attempted to close a non-existent rec.")
        

    # Manually add a (most likely closed) rating
    @classmethod
    async def add_rating_manual(cls, rec: Recommendation) -> None:
        if not await cls._does_user_exist(rec.rater):
            await cls._add_user(rec.rater)
        if not await cls._does_user_exist(rec.suggester):
            await cls._add_user(rec.suggester)
        if not await cls._does_song_exist(rec.song):
            await cls._add_song(rec.song)
        if await cls._does_rating_exist(rec):
            raise ValueError("Attempted to create a pre-existing rec.")
        else:
            await cls._add_rec_manual(rec)
            cls.con.commit()

    @classmethod
    async def create_thread(cls, thread: Thread) -> None:
        if not await cls._does_user_exist(thread.user1):
            await cls._add_user(thread.user1)
        if not await cls._does_user_exist(thread.user2):
            await cls._add_user(thread.user2)
        if await cls._does_thread_exist(thread=thread):
            raise ValueError("Attempted to create a pre-existing thread")
        else:
            await cls._add_thread(thread)
            cls.con.commit()

    @classmethod
    async def get_thread_by_id(cls, thread_id: int) -> Thread:
        if await cls._does_thread_exist(thread_id=thread_id):
            cls.cur.execute(
                '''SELECT * FROM thread where thread_id = ?''',
                (thread_id,)
            )
            return Thread.parse_tuple(cls.cur.fetchone())
        else:
            raise ValueError("Command not used in an established thread.")

    @classmethod
    async def flip_thread(cls, thread: Thread, next_user: User = None) -> Thread:
        next_user = next_user or thread.other_user
        if await cls._does_thread_exist(thread=thread):
            cls.cur.execute(
                '''UPDATE thread SET next_user = ? WHERE thread_id = ?''',
                (next_user.discord_id, thread.thread_id)
            )
            cls.con.commit()
        thread.next_user = next_user
        return thread

    @classmethod
    async def get_waiting_threads_by_user(cls, user: User) -> List[Thread]:
        cls.cur.execute('''
                SELECT * FROM thread WHERE next_user = ?
            ''',
            (user.discord_id,)
        )
        return Thread.parse_tuples(cls.cur.fetchall())

    # Fetch the open rec (if any) in a thread
    @classmethod
    async def get_open_rating_by_thread(cls, thread: Thread) -> Optional[Recommendation]:
        cls.cur.execute('''
                SELECT * FROM recommendation
                WHERE rater_id = ? AND suggester_id = ? AND is_closed = 0
            ''',
            (thread.next_user.discord_id, thread.other_user.discord_id)    
        )
        return Recommendation.parse_tuple(cls.cur.fetchone())
    
    @classmethod
    async def get_ratings_by_suggester(cls, suggester: User, is_closed = 1) -> List[Recommendation]:
        cls.cur.execute('''
                SELECT * FROM recommendation 
                WHERE suggester_id = ? AND is_closed = ?
            ''', 
            (suggester.discord_id, is_closed)
        )
        # Parse elements into dataclass in schema order 
        return Recommendation.parse_tuples(cls.cur.fetchall())

    # These two functions fetch all recommendations for a specific rater, either closed or open.
    @classmethod
    async def get_ratings_by_rater(cls, rater: User, is_closed = 1) -> List[Recommendation]:
        cls.cur.execute('''
                SELECT * FROM recommendation 
                WHERE rater_id = ? AND is_closed = ?
            ''', 
            (rater.discord_id, is_closed)
        )
        # Parse elements into dataclass in schema order 
        return Recommendation.parse_tuples(cls.cur.fetchall())

    @classmethod
    async def get_open_recs_by_rater(cls, rater: User) -> List[Recommendation]:
       return await cls.get_ratings_by_rater(rater, is_closed=0)

    # Fetch all recommendations of a specific song
    @classmethod
    async def get_ratings_by_song(cls, song: Song) -> List[Recommendation]:
        cls.cur.execute('''
                SELECT * FROM recommendation 
                WHERE song_name = ? AND artist = ? AND is_closed = 1
            ''', 
            (song.name, song.artist)
        )
        return Recommendation.parse_tuples(cls.cur.fetchall())

    # Used for rerate() method
    @classmethod
    async def get_ratings_by_song_and_pair(cls, song: Song, rater: User, suggester:User) -> List[Recommendation]:
        print(f'''
                SELECT * FROM recommendation 
                WHERE song_name = {song.name} AND artist = {song.artist} AND is_closed = 1 AND rater_id = {rater.discord_id} AND suggester_id = {suggester.discord_id}
            ''')
        cls.cur.execute('''
                SELECT * FROM recommendation 
                WHERE song_name = ? AND artist = ? AND is_closed = 1 AND rater_id = ? AND suggester_id = ?
            ''', 
            (song.name, song.artist, rater.discord_id, suggester.discord_id)
        )
        return Recommendation.parse_tuples(cls.cur.fetchall())
    
    # Fetch all recommendations of a specific artist
    @classmethod
    async def get_ratings_by_artist(cls, artist) -> List[Recommendation]:
        cls.cur.execute('''
                SELECT * FROM recommendation 
                WHERE artist = ? AND is_closed = 1
            ''', (artist,)
        )
        return Recommendation.parse_tuples(cls.cur.fetchall())

    # Takes two user IDs and returns all ratings between the two
    @classmethod
    async def get_ratings_by_pair(cls, a: User, b: User) -> List[Recommendation]:
        cls.cur.execute('''
                SELECT * FROM recommendation 
                WHERE rater_id IN (:a, :b) and suggester_id in (:a, :b) AND is_closed = 1
                ORDER BY timestamp desc
            ''', 
            {"a": a.discord_id, "b": b.discord_id}
        )
        return Recommendation.parse_tuples(cls.cur.fetchall())


    #takes two user IDs as inputs and returns all songs they have both rated
    @classmethod
    async def get_overlap(cls, rater_a: User, rater_b: User) -> List[Tuple[Recommendation]]:
        cls.cur.execute('''
                SELECT 
                    a.song_name, a.artist, a.guild_id,
                    a.suggester_id, a.timestamp, a.rating_a, 
                    b.suggester_id, b.timestamp, b.rating_b
                    FROM (
                        SELECT max(rating) rating_a, song_name, artist, timestamp, rater_id, suggester_id, guild_id
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
                    suggester=User(discord_id=item[3]),
                    guild=Guild(item[2]),
                    timestamp=item[4],
                    rating=item[5],
                    is_closed=True
                ),
                Recommendation(
                    song=Song(name=item[0], artist=item[1]),
                    rater=rater_b,
                    suggester=User(discord_id=item[6]),
                    guild=Guild(item[2]),
                    timestamp=item[7],
                    rating=item[8],
                    is_closed=True
                )
            )
            for item in cls.cur.fetchall()
        ]
    
    #This returns a list, even though it is a superlative, because two recommendations may share a max rating   
    @classmethod
    async def get_max_rating(cls, suggester : User, rater : User = None) -> List[Recommendation]:
        #print("suggester: {suggester}, rater: {rater}".format(suggester=suggester.discord_id, rater=rater.discord_id))        
        if rater == None:
            print 
            cls.cur.execute('''
                SELECT * FROM recommendation 
                    WHERE suggester_id = :suggester
                    AND rating = (
                        SELECT MAX(rating) FROM recommendation WHERE suggester_id = :suggester
                    )
                ''',
                {"suggester": suggester.discord_id}
                
            )
            return Recommendation.parse_tuples(cls.cur.fetchall())            
        else:
            cls.cur.execute('''
                SELECT * FROM recommendation 
                    WHERE suggester_id = :suggester AND rater_id = :rater
                    AND rating = (
                        SELECT MAX(rating) FROM recommendation WHERE suggester_id = :suggester AND rater_id = :rater
                    )
                ''',
                {"suggester": suggester.discord_id, "rater": rater.discord_id}
            )
            return Recommendation.parse_tuples(cls.cur.fetchall())

    @classmethod
    async def get_average_rating(cls, suggester : User, rater : User = None) -> float:
        if rater == None:
            cls.cur.execute('''
                SELECT AVG(rating) FROM recommendation 
                    WHERE suggester_id = :suggester
                    AND is_closed 
                ''',
                {"suggester": suggester.discord_id}
            )
            return cls.cur.fetchone()[0]
        else:
            cls.cur.execute('''
                SELECT AVG(rating) FROM recommendation 
                    WHERE suggester_id = :suggester
                    AND rater_id = :rater
                    AND is_closed
                ''',
                {"suggester": suggester.discord_id, "rater": rater.discord_id}
            )
            return cls.cur.fetchone()[0]

    @classmethod
    async def get_total_rating(cls, suggester : User, rater : User = None) -> float:
        if rater == None:
            cls.cur.execute('''
                SELECT SUM(rating) FROM recommendation 
                    WHERE suggester_id = ? 
                    AND is_closed
                ''',(suggester.discord_id,)
            )
            return cls.cur.fetchone()[0]
        else:
            cls.cur.execute('''
                SELECT SUM(rating) FROM recommendation 
                    WHERE suggester_id = ? 
                    AND rater_id = ?
                    AND is_closed
                ''',(suggester.discord_id, rater.discord_id)
            )
            return cls.cur.fetchone()[0]
           
    @classmethod
    async def get_max_ratings(cls, rater : User = None) -> List[Recommendation]:
        if rater:
            cls.cur.execute('''
                SELECT song_name, artist, rater_id, suggester_id, guild_id, timestamp, MAX(rating) as rating, is_closed \
                    FROM recommendation 
                    WHERE is_closed
                    AND rater_id = ?
                    GROUP BY suggester_id 
                    ORDER BY rating DESC
                ''', (rater.discord_id,))
            return Recommendation.parse_tuples(cls.cur.fetchall())
        else:
            cls.cur.execute('''
                SELECT song_name, artist, rater_id, suggester_id, guild_id, timestamp, MAX(rating) as rating, is_closed \
                    FROM recommendation 
                    WHERE is_closed
                    GROUP BY suggester_id 
                    ORDER BY rating DESC
            ''')
            return Recommendation.parse_tuples(cls.cur.fetchall())

    @classmethod
    async def get_average_ratings(cls, rater : User = None) -> Tuple[float, User]:
        if rater == None:
            cls.cur.execute('''
                SELECT AVG(rating) as avg_rating, suggester_id 
                    FROM recommendation 
                    WHERE is_closed
                    GROUP BY suggester_id 
                    ORDER BY avg_rating DESC
                ''')
            return [(rating, User(id)) for rating, id in cls.cur.fetchall()]
        else:
            cls.cur.execute('''
                SELECT AVG(rating) as avg_rating, suggester_id 
                    FROM recommendation 
                    WHERE is_closed
                    AND rater_id = ?
                    GROUP BY suggester_id 
                    ORDER BY avg_rating DESC
                ''', (rater.discord_id,))
            return [(rating, User(id)) for rating, id in cls.cur.fetchall()]


    @classmethod
    async def get_total_ratings(cls, rater : User = None) -> Tuple[float, User]:
        if rater == None:
            cls.cur.execute('''
                SELECT SUM(rating) as total_rating, suggester_id 
                    FROM recommendation 
                    WHERE is_closed
                    GROUP BY suggester_id 
                    ORDER BY total_rating DESC
                ''')
            return [(rating, User(id)) for rating, id in cls.cur.fetchall()]
        else:
            cls.cur.execute('''
                SELECT SUM(rating) as total_rating, suggester_id 
                    FROM recommendation 
                    WHERE is_closed
                    AND rater_id = ?
                    GROUP BY suggester_id 
                    ORDER BY total_rating DESC
                ''', (rater.discord_id,))
            return [(rating, User(id)) for rating, id in cls.cur.fetchall()]


    




async def lame_ass_test_suite():
    backEnd = DB(True)
    print("Running initial tests:")
    user1 = User(12345)
    await backEnd._add_user(user1)
    print(await backEnd._does_user_exist(user1))
    print(not await backEnd._does_user_exist(User(58613)))
    user2 = User(3)
    await backEnd._add_user(user2)
    print(await backEnd._does_user_exist(user2))

    sandstorm = Song("Sandstorm", "Darude")
    await backEnd._add_song(sandstorm)
    print(await backEnd._does_song_exist(sandstorm))
    print(not await backEnd._does_song_exist(Song("Sandstorm", "dadude")))
    print(await backEnd._does_song_exist(sandstorm))
    rec1 = Recommendation(
        song=sandstorm, 
        rater=user1, 
        suggester=user2,
        guild=Guild(1048),
        timestamp=datetime.now(),
        rating=10,
        is_closed=True
    )
    await backEnd.add_rating_manual(rec1)
    print(await backEnd._does_rating_exist(rec1))
    print(
        not await backEnd._does_rating_exist(
            Recommendation(
                Song("Sandstorm", "DaDude"), 
                User(12345), 
                User(3),
                Guild(1048),
                datetime.now(),
            )
        )
    )
    print("\n")


    #ID 1 suggests a few songs, they are rated
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Goodbye", "AREZRA"), 
            User(12345), 
            User(1), 
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=10, 
            is_closed=True
        )
    )
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Goodbye", "AREZRA"), 
            User(2), 
            User(1),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=6, 
            is_closed=True
        )
    )
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Goodbye", "AREZRA"), 
            User(3), 
            User(1),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=8, 
            is_closed=True
        )
    )
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Goodbye", "AREZRA"), 
            User(4), 
            User(1),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=5, 
            is_closed=True
        )
    )

    #users suggest songs back
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Drowning", "AREZRA"), 
            User(1), 
            User(12345),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=8, 
            is_closed=True
        )
    )
    await backEnd.add_rating_manual(
        Recommendation(
            Song("My Son John", "Smokey Bastard"), 
            User(1), 
            User(2),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=6, 
            is_closed=True
        )
    )
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Time Bomb", "Feint"), 
            User(1), 
            User(3),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=7, 
            is_closed=True
        )
    )
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Dead Inside", "Younger Hunger"), 
            User(1), 
            User(4),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=3, 
            is_closed=True
        )
    )
    
    #some inter-user rating goes on
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Drowning", "AREZRA"), 
            User(3), 
            User(2),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=8, 
            is_closed=True
        )
    )
    #Two ratings for the same song by the same user
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Drowning", "AREZRA"), 
            User(3), 
            User(4),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=7, 
            is_closed=True
        )
    )
    await backEnd.add_rating_manual(
        Recommendation(
            Song("Dead Inside", "Younger Hunger"), 
            User(3), 
            User(2),
            guild=Guild(1048),
            timestamp=datetime.now(), 
            rating=5, 
            is_closed=True
        )
    )
    print("Ratings of Goodbye:")
    pprint(await backEnd.get_ratings_by_song(Song("goodbye", "arezra")))
    print("Ratings of arezra:")
    pprint(await backEnd.get_ratings_by_artist("arezra"))
    print("User 2's ratings:")
    pprint(await backEnd.get_ratings_by_rater(User(2)))
    print("User 3's ratings:")
    pprint(await backEnd.get_ratings_by_rater(User(3)))

    print("Ratings between users 2 and 3")
    pprint(await backEnd.get_ratings_by_pair(User(2),User(3)))

    print("Overlap between 1 and 3")
    pprint(await backEnd.get_overlap(User(1),User(3)))

    print("User 2's ratings:")
    pprint(await backEnd.get_ratings_by_rater(User(2)))

    print("Overlap between 2 and 3")
    pprint(await backEnd.get_overlap(User(2),User(3)))

if __name__ == "__main__":
    import asyncio
    asyncio.run(lame_ass_test_suite())