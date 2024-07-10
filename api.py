import sqlite3

from fastapi import Body, FastAPI, HTTPException, Query
from pydantic import BaseModel

# Создаем приложение FastAPI
app = FastAPI()

# Подключаемся к базе данных SQLite
conn = sqlite3.connect("ads.db", check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу 'ads', если она еще не существует
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        photos TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)
conn.commit()


# Модель для данных объявления
class Ad(BaseModel):
    user_id: int
    text: str
    photos: str


# Модель для ответа с данными объявления
class AdOut(BaseModel):
    id: int
    user_id: int
    text: str
    photos: str
    created_at: str


# Обработчик для создания объявления
@app.post("/ads/", response_model=AdOut)
def create_ad(ad: Ad = Body(...)):
    cursor.execute(
        """
        INSERT INTO ads (user_id, text, photos)
        VALUES (?, ?, ?)
    """,
        (ad.user_id, ad.text, ad.photos),
    )
    conn.commit()
    ad_id = cursor.lastrowid

    return {
        "id": ad_id,
        "user_id": ad.user_id,
        "text": ad.text,
        "photos": ad.photos,
        "created_at": None,  # Created automatically by SQLite
    }


# Обработчик для получения всех объявлений
@app.get("/ads/", response_model=list[AdOut])
def read_ads():
    cursor.execute("SELECT * FROM ads")
    ads = cursor.fetchall()

    return [
        {
            "id": ad[0],
            "user_id": ad[1],
            "text": ad[2],
            "photos": ad[3],
            "created_at": ad[4],
        }
        for ad in ads
    ]


# Обработчик для получения объявления по ID
@app.get("/ads/{ad_id}", response_model=AdOut)
def read_ad(ad_id: int):
    cursor.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    ad = cursor.fetchone()

    if ad:
        return {
            "id": ad[0],
            "user_id": ad[1],
            "text": ad[2],
            "photos": ad[3],
            "created_at": ad[4],
        }
    else:
        raise HTTPException(status_code=404, detail="Ad not found")


# Обработчик для удаления объявления по ID
@app.delete("/ads/{ad_id}")
def delete_ad(ad_id: int):
    cursor.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
    conn.commit()
    return {"message": "Ad deleted successfully"}


# Запускаем сервер FastAPI
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
