import sqlite3

class BackEnd():
    def __init__(self, truncate=False) -> None:
        self.con = sqlite3.connect("pyrate.db")
        self.cur = self.con.cursor()
        self.cur.execute('PRAGMA foreign_keys = ON')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS user(
            discord_id NUMERIC PRIMARY KEY NOT NULL
            );
        ''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS song(
            song_name varchar NOT NULL COLLATE NOCASE,
            artist varchar NOT NULL COLLATE NOCASE,
            PRIMARY KEY(song_name, artist)
            );
        ''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS rating(
            song_name varchar NOT NULL COLLATE NOCASE,
            artist varchar NOT NULL COLLATE NOCASE,
            rater_id NUMERIC NOT NULL,
            suggester_id NUMERIC NOT NULL,
            rating NUMERIC NOT NULL,
            timestamp text NOT NULL,
            FOREIGN KEY (song_name, artist) REFERENCES song (song_name, artist)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            FOREIGN KEY (rater_id) REFERENCES user (discord_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            FOREIGN KEY (suggester_id) REFERENCES user (discord_id)
                ON DELETE CASCADE
                ON UPDATE CASCADE)
        ''')
        if truncate:
            self.cur.execute('DELETE FROM user')
            self.cur.execute('DELETE FROM song')
            self.cur.execute('DELETE FROM rating')

    def add_user(self, id) -> None:
        self.cur.execute('''INSERT INTO user VALUES(?)''', (id,))
    def does_user_exist(self, id) -> bool:
        self.cur.execute('''SELECT * FROM user WHERE discord_id = ?''', (id,))
        res = self.cur.fetchone()
        return bool(res)

    def add_song(self, name, artist) -> None:
        self.cur.execute('''INSERT INTO song VALUES(?, ?)''', (name, artist))
    def does_song_exist(self, name, artist) -> bool:
        self.cur.execute('''SELECT * FROM song WHERE song_name = ? and artist = ?''', (name, artist))
        res = self.cur.fetchone()
        return bool(res)

    def add_rating(self, song_name, artist, rater_id, suggester_id, rating) -> None:
        self.cur.execute('''INSERT INTO rating VALUES(?, ?, ?, ?, ?, datetime())''',
             (song_name, artist, rater_id, suggester_id, rating))
    def update_rating(self, song_name, artist, rater_id, suggester_id, rating) -> None:
        self.cur.execute('''UPDATE rating SET rating = ? WHERE song_name = ? AND artist = ? AND rater_id = ? AND suggester_id = ?''',
             (rating, song_name, artist, rater_id, suggester_id))
    def does_rating_exist(self, song_name, artist, rater_id, suggester_id) -> bool:
        self.cur.execute('''SELECT * FROM rating WHERE song_name = ? AND artist = ? AND rater_id = ? AND suggester_id = ?''',
            (song_name, artist, rater_id, suggester_id))
        res = self.cur.fetchone()
        return bool(res)

    #this function handles checks for existance of user, song, and rating
    def rate(self, song_name, artist, rater_id, suggester_id, rating) -> None:

        if not self.does_user_exist(rater_id):
            self.add_user(rater_id)
        if not self.does_user_exist(suggester_id):
            self.add_user(suggester_id)

        if not self.does_song_exist(song_name, artist):
            self.add_song(song_name, artist)

        if self.does_rating_exist(song_name, artist, rater_id, suggester_id):
            self.update_rating(song_name, artist, rater_id, suggester_id, rating)
        else:
            self.add_rating(song_name, artist, rater_id, suggester_id, rating)
        self.con.commit()
    

    #The following functions return tuples following the pattern song_name, artist, rater_id, suggester_id, and finally rating. Any fields used to query will be omitted from the tuple

    #returns a list of tuples consisting of song_name, artist, suggester, and rating
    def get_ratings_by_rater(self, rater_id) -> tuple:
        self.cur.execute("SELECT song_name, artist, suggester_id, rating FROM rating WHERE rater_id = ?", (rater_id,))
        return self.cur.fetchall()
    
    #returns a list of tuples consisting of rater_id, suggester_id, and rating for a specific song
    def get_ratings_by_song(self, song_name, artist) -> tuple:
        self.cur.execute("SELECT rater_id, suggester_id, rating FROM rating WHERE song_name = ? and artist = ?", (song_name, artist))
        return self.cur.fetchall()
    
    #returns a list of tuples consisting of song_name, rater_id, suggester_id, and rating for a specific song
    def get_ratings_by_artist(self,artist) -> tuple:
        self.cur.execute("SELECT song_name, rater_id, suggester_id, rating FROM rating WHERE artist = ?", (artist,))
        return self.cur.fetchall()

    #takes two user IDs and returns all ratings between the two
    #returns a list of tuples consisting of song_name, artist, rater_id, suggester_id, and rating
    def get_ratings_by_pair(self, user_a, user_b):
        self.cur.execute("SELECT song_name, artist, rater_id, suggester_id, rating FROM rating WHERE rater_id IN (:a, :b) and suggester_id in (:a, :b)", {"a": user_a, "b": user_b})
        return self.cur.fetchall()
    


    #takes two user IDs as inputs and returns all songs they have both rated
    #returns a list of tuples consisting of song_name, artist_name, user_a rating, and user_b rating
    def get_overlap(self, rater_a, rater_b):
        self.cur.execute('''SELECT a.song_name, a.artist, a.rating_a, b.rating_b
            FROM (SELECT max(rating) rating_a, song_name, artist FROM rating WHERE rater_id = ? GROUP BY song_name, artist) a
            INNER JOIN (SELECT max(rating) rating_b, song_name, artist FROM rating WHERE rater_id = ? GROUP BY song_name, artist) b
            ON a.song_name = b.song_name AND a.artist = b.artist''', (rater_a, rater_b))
        return self.cur.fetchall()


    




if __name__ == "__main__":
    backEnd = BackEnd(True)
    print("Running initial tests:")
    backEnd.add_user(12345)
    print(backEnd.does_user_exist(12345))
    print(not backEnd.does_user_exist(58613))
    backEnd.add_user(3)
    print(backEnd.does_user_exist(3))

    backEnd.add_song("Sandstorm", "Darude")
    print(backEnd.does_song_exist("Sandstorm", "Darude"))
    print(backEnd.does_song_exist("sandstorm", "darude"))
    print(not backEnd.does_song_exist("Sandstorm", "dadude"))
    print(backEnd.does_song_exist("sandstorm", "darude"))
    backEnd.add_rating("Sandstorm", "Darude", 12345, 3, 10)
    print(backEnd.does_rating_exist("Sandstorm", "Darude", 12345, 3))
    print(not backEnd.does_rating_exist("Sandstorm", "DaDude", 12345, 3))
    print("\n")


    #ID 1 suggests a few songs, they are rated
    backEnd.rate("Goodbye", "AREZRA", 12345, 1, 10)
    backEnd.rate("Goodbye", "AREZRA", 2, 1, 6)
    backEnd.rate("Goodbye", "AREZRA", 3, 1, 8)
    backEnd.rate("Goodbye", "AREZRA", 4, 1, 5)

    #users suggest songs back
    backEnd.rate("Drowning", "AREZRA", 1, 12345, 8)
    backEnd.rate("My Son John", "Smokey Bastard", 1, 2, 6)
    backEnd.rate("Time Bomb", "Feint", 1, 3, 7)
    backEnd.rate("Dead Inside", "Younger Hunger", 1, 4, 3)
    
    #some inter-user rating goes on
    backEnd.rate("Drowning", "AREZRA", 3, 2, 8)
    backEnd.rate("Goodbye", "AREZRA", 2, 3, 7) #Two ratings for the same song by the same user
    backEnd.rate("Dead Inside", "Younger Hunger", 3, 2, 5)
    print("Ratings of Goodbye:")
    print(backEnd.get_ratings_by_song("goodbye", "arezra"))
    print("Ratings of arezra:")
    print(backEnd.get_ratings_by_artist("arezra"))
    print("User 2's ratings:")
    print(backEnd.get_ratings_by_rater(2))
    print("User 3's ratings:")
    print(backEnd.get_ratings_by_rater(3))

    print("Ratings between users 2 and 3")
    print(backEnd.get_ratings_by_pair(2,3))

    print("Overlap between 1 and 3")
    print(backEnd.get_overlap(1,3))

    print("User 2's ratings:")
    print(backEnd.get_ratings_by_rater(2))

    print("Overlap between 2 and 3")
    print(backEnd.get_overlap(2,3))


    
else:
    backEnd = BackEnd()
