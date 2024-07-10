import sqlite3

conn = sqlite3.connect("ads.db", check_same_thread=False)
cursor = conn.cursor()


def init_db():
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            photos TEXT NOT NULL,
            rooms INTEGER,
            price REAL,
            type TEXT,
            area TEXT,
            house_name TEXT,
            district TEXT,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()


def save_ad_to_db(user_id, data):
    photos_str = ",".join(
        data["photos"]
    )  # Store photo file IDs as a comma-separated string
    cursor.execute(
        """
        INSERT INTO ads (user_id, username, photos, rooms, price, type, area, house_name, district, text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            data["username"],
            photos_str,
            data["rooms"],
            data["price"],
            data["type"],
            data["area"],
            data["house_name"],
            data["district"],
            data["text"],
        ),
    )
    conn.commit()
    return cursor.lastrowid


def fetch_ad_by_id(ad_id):
    cursor.execute(
        "SELECT username, photos, rooms, price, type, area, house_name, district, text FROM ads WHERE id = ?",
        (ad_id,),
    )
    row = cursor.fetchone()
    if row:
        username, photos_str, rooms, price, type, area, house_name, district, text = row
        photos = photos_str.split(
            ","
        )  # Convert the comma-separated string back to a list
        return (username, photos, rooms, price, type, area, house_name, district, text)
    return None
